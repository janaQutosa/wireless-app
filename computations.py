import math

def compute_wireless_system(inputs):
    """
    Models the data rate through a digital communication system pipeline,
    from sampling to transmission, accounting for compression, coding, and overhead.
    Input 'inputs' is a dictionary with keys:
        - sampling_rate: in MHz
        - bits_per_sample: number of bits
        - compression_ratio: >0
        - code_rate: (0 < r ≤ 1)
        - overhead: in percent (e.g., 20 means +20%)
    Output: dictionary of data rates at each block in Mbps.
    """
    # Extract inputs with defaults
    fs_mhz = float(inputs.get("sampling_rate", 0))
    fs = fs_mhz * 1e6  # Convert MHz to Hz

    b = float(inputs.get("bits_per_sample", 0))
    cr = float(inputs.get("compression_ratio", 1))
    r = float(inputs.get("code_rate", 1))
    overhead = float(inputs.get("overhead", 0)) / 100  # percent to fraction

    # Validate inputs
    if fs <= 0 or b <= 0:
        raise ValueError("sampling_rate and bits_per_sample must be > 0")
    if cr <= 0:
        raise ValueError("compression_ratio must be > 0")
    if not (0 < r <= 1):
        raise ValueError("code_rate must be in (0, 1]")
    
    results = {}

    # Sampler: samples per second in MHz
    results["sampler"] = fs * b / 1e6  # in Mbps

    # Quantizer: samples × bits/sample → bit rate
    quantizer_rate = fs * b  # bits/sec
    results["quantizer"] = quantizer_rate / 1e6  # Mbps

    # Source encoder: apply compression
    source_encoded_rate = quantizer_rate / cr
    results["source_encoder"] = source_encoded_rate / 1e6

    # Channel encoder: add redundancy
    channel_encoded_rate = source_encoded_rate / r
    results["channel_encoder"] = channel_encoded_rate / 1e6

    # Interleaver: no change
    results["interleaver"] = results["channel_encoder"]

    # Burst formatter: add overhead
    burst_formatted_rate = channel_encoded_rate * (1 + overhead)
    results["burst_formatter"] = burst_formatted_rate / 1e6

    return results



#--------------------------------------------------------------------------------------------------------


def compute_ofdm_system(inputs):
    """
    Computes theoretical data rate and spectral efficiency of an OFDM system,
    such as LTE or 5G, based on physical layer parameters.
    """

    # Input Parameters
    delta_f = float(inputs.get("subcarrier_spacing", 0)) * 1e3  # kHz → Hz
    n_sc = int(inputs.get("subcarriers_per_rb", 12))
    n_sym = int(inputs.get("symbols_per_slot", 14))
    m = int(inputs.get("modulation_order", 4))
    n_rb = int(inputs.get("resource_blocks", 0))
    bw = float(inputs.get("bandwidth", 0)) * 1e6  # MHz → Hz
    r = float(inputs.get("code_rate", 1))

    # Input validation
    if delta_f <= 0:
        raise ValueError("subcarrier_spacing must be > 0")
    if m < 2:
        raise ValueError("modulation_order must be ≥ 2")
    if n_rb <= 0:
        raise ValueError("resource_blocks must be > 0")
    if bw <= 0:
        raise ValueError("bandwidth must be > 0")
    if not (0 < r <= 1):
        raise ValueError("code_rate must be in (0, 1]")

    # Compute numerology index μ
    mu = round(math.log2(delta_f / 15e3))

    # Slot duration in seconds
    slot_duration = 1e-3 / (2 ** mu)

    # Bits per resource element (RE)
    bits_per_re = math.log2(m) * r

    # Total REs per slot
    total_re_per_slot = n_rb * n_sc * n_sym

    # Capacity (bps): total bits per slot / slot duration
    capacity_bps = total_re_per_slot * bits_per_re / slot_duration

    results = {
        "resource_element": bits_per_re,  # bits per RE
        "ofdm_symbol": n_rb * n_sc * bits_per_re,  # bits per OFDM symbol across RBs
        "resource_block": n_sc * n_sym * bits_per_re,  # bits per RB per slot
        "capacity": capacity_bps / 1e6,  # Mbps
        "spectral_efficiency": capacity_bps / bw  # bps/Hz
    }

    return results


#--------------------------------------------------------------------------------------------------------



EB_N0_MAP = {
    "BPSK/QPSK": {
        1e-1: 0,
        1e-2: 4,
        1e-3: 7,
        1e-4: 8.3,
        1e-5: 9.6,
        1e-6: 10.5,
        1e-7: 11.6,
        1e-8: 12,
    },
    
    "8-PSK": {
        1e-1: 0,
        1e-2: 6.5,
        1e-3: 10,
        1e-4: 12,
        1e-5: 12.5,
        1e-6: 14,
        1e-7: 14.7,
        1e-8: 15.6,
    },
    "16-PSK": {
        1e-1: 0,
        1e-2: 10.5,
        1e-3: 14.1,
        1e-4: 16,
        1e-5: 17.7,
        1e-6: 18.3,
        1e-7: 19.2,
        1e-8: 20,
    }
}


def compute_link_budget(inputs):
    # Extract inputs
    p_tx = float(inputs.get("tx_power", 0))         # dBm
    g_tx = float(inputs.get("tx_gain", 0))          # dBi
    g_rx = float(inputs.get("rx_gain", 0))          # dBi
    pl = float(inputs.get("path_loss", 0))          # dB
    l_other = float(inputs.get("other_losses", 0))  # dB
    modulation = inputs.get("modulation", "BPSK/QPSK")
    ber = float(inputs.get("ber", 1e-3))
    nf = float(inputs.get("noise_figure", 0))       # dB
    r = float(inputs.get("data_rate", 0)) * 1e3     # kbps → bps

    k = 1.38e-23    # Boltzmann constant
    t = 290         # Temperature K

    # Noise figure linear
    f_linear = 10 ** (nf / 10)

    # Received power
    p_rx = p_tx + g_tx + g_rx - pl - l_other  # dBm

    # Lookup / interpolate Eb/N0
    eb_n0_map = EB_N0_MAP.get(modulation, EB_N0_MAP["BPSK/QPSK"])
    ber_keys = sorted(eb_n0_map.keys())
    eb_n0_required = None

    for i in range(len(ber_keys) - 1):
        if ber_keys[i] <= ber <= ber_keys[i+1]:
            eb_n0_required = eb_n0_map[ber_keys[i]] + \
                (eb_n0_map[ber_keys[i+1]] - eb_n0_map[ber_keys[i]]) * \
                ((ber - ber_keys[i]) / (ber_keys[i+1] - ber_keys[i]))
            break

    if eb_n0_required is None:
        if ber < ber_keys[-1]:
            eb_n0_required = eb_n0_map[ber_keys[-1]]  # Conservative
        else:
            eb_n0_required = eb_n0_map[ber_keys[0]]   # Optimistic

    # Convert Eb/N0 dB → linear
    eb_n0_linear = 10 ** (eb_n0_required / 10)

    # Pr in watts
    pr_watts = 10 ** ((p_rx - 30) / 10)

    # Denominator: k * T * F * R * Eb/N0
    denominator = k * t * f_linear * r * eb_n0_linear
    m_linear = pr_watts / denominator if denominator > 0 else 0
    m_db = 10 * math.log10(m_linear) if m_linear > 0 else float('-inf')

    return {
        "received_power_dBm": p_rx,
        "eb_n0_required_dB": eb_n0_required,
        "link_margin_dB": m_db
    }


#--------------------------------------------------------------------------------------------------------


def compute_cellular_design(inputs):
    # Extract inputs
    P_ref = float(inputs.get("P_ref", -22.0))  # Reference power at 10 m in dBm
    n = float(inputs.get("path_loss_exponent", 3.0))
    P_sensitivity = float(inputs.get("receiver_sensitivity", 7e-6))  # Watts
    SIR_dB = float(inputs.get("SIR_dB", 13.0))
    A_city = float(inputs.get("city_area", 4e6))  # m^2
    N_subscribers = int(inputs.get("subscribers", 80000))
    calls_per_day = float(inputs.get("calls_per_day", 8.0))
    call_duration = float(inputs.get("call_duration", 3.0))  # minutes
    GoS = float(inputs.get("GoS", 0.02))
    timeslots_per_carrier = int(inputs.get("timeslots_per_carrier", 8))

    # Helpers
    def watts_to_dBm(P_watts):
        return 10 * math.log10(P_watts) + 30

    # a) Max distance
    P_sensitivity_dBm = watts_to_dBm(P_sensitivity)
    path_loss_dB = P_ref - P_sensitivity_dBm
    d_max = 10 * (10 ** (path_loss_dB / (10 * n)))  # d0=10 m

    # b) Cell area (hex)
    R = d_max
    A_cell = (3 * math.sqrt(3) / 2) * R**2

    # c) Number of cells
    N_cells = math.ceil(A_city / A_cell)

    # d) Total traffic
    calls_per_hour = calls_per_day / 24
    traffic_per_subscriber = calls_per_hour * (call_duration/60)  # minutes→hours→Erlangs
    A_total = N_subscribers * traffic_per_subscriber

    # e) Traffic per cell
    A_per_cell = A_total / N_cells

    # f) Cluster size
    SIR_linear = 10 ** (SIR_dB/10)
    # SIR ≈ (D/R)^n / 6 ⇒ (D/R) = (SIR*6)^{1/n} ⇒ D=R*(SIR*6)^{1/n}
    D_over_R = (SIR_linear*6)**(1/n)
    K = (D_over_R**2)/3
    K = math.ceil(K)
    valid_K = [1,3,4,7,9,12,13,19]
    K = min([k for k in valid_K if k>=K], default=7)

    # g) Number of carriers
    def find_channels(traffic, gos):
        table = {
            0.02: {2.3:6, 3.6:8, 4.3:9, 5.1:10, 5.8:11, 6.6:12, 7.4:13, 8.1:14, 8.9:15, 9.7:16},
            0.05: {3.0:6, 4.5:8, 5.4:9, 6.2:10, 7.1:11, 8.0:12, 9.0:13, 9.8:14, 10.6:15, 11.5:16}
        }[gos]
        for t in sorted(table):
            if traffic <= t:
                return table[t]
        return math.ceil(traffic)+1

    N_channels_per_cell = find_channels(A_per_cell, GoS)
    N_carriers_per_cell = math.ceil(N_channels_per_cell / timeslots_per_carrier)
    N_total_carriers = N_carriers_per_cell * N_cells

    # Optional: for GoS=0.05
    N_channels_5 = find_channels(A_per_cell, 0.05)
    N_carriers_5 = math.ceil(N_channels_5 / timeslots_per_carrier)
    N_total_5 = N_carriers_5 * N_cells

    return {
        "max_distance_m": d_max,
        "cell_area_m2": A_cell,
        "num_cells": N_cells,
        "total_traffic_erlangs": A_total,
        "traffic_per_cell_erlangs": A_per_cell,
        "cluster_size": K,
        "total_carriers_GoS_0.02": N_total_carriers,
        "total_carriers_GoS_0.05": N_total_5
    }
