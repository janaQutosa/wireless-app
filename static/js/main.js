document.addEventListener("DOMContentLoaded", () => {
    const forms = {
        "wireless-form": "/wireless",
        "ofdm-form": "/ofdm",
        "link-budget-form": "/link_budget",
        "cellular-form": "/cellular"
    };

    Object.keys(forms).forEach(formId => {
        const form = document.getElementById(formId);
        if (form) {
            form.addEventListener("submit", async (e) => {
                e.preventDefault();

                const formData = new FormData(form);
                const response = await fetch(forms[formId], {
                    method: "POST",
                    body: formData
                });

                const resultsDiv = document.getElementById("results");
                const resultsTable = document.getElementById("results-table");
                const explanation = document.getElementById("explanation");
                const chartCanvas = document.getElementById("results-chart");

                if (response.ok) {
                    const data = await response.json();

                    // Populate results table
                    resultsTable.innerHTML = "";
                    let labels = [];
                    let values = [];

                    for (const [key, value] of Object.entries(data.results)) {
                        const row = document.createElement("tr");
                        row.innerHTML = `<td class="p-2">${key.replace("_", " ")}</td><td class="p-2">${value.toFixed(2)}</td>`;
                        resultsTable.appendChild(row);
                        labels.push(key.replace("_", " "));
                        values.push(value);
                    }

                    // Format explanation JSON nicely
                    explanation.innerHTML = "";
                    try {
    const parsed = typeof data.explanation === "string" ? JSON.parse(data.explanation) : data.explanation;

    let explanationHTML = `
        <h4 class="font-bold text-lg mb-2">${parsed.title}</h4>
        <p class="mb-3">${parsed.methodology}</p>
        <h5 class="font-semibold mt-3">Components:</h5>
        <ul class="list-disc list-inside mb-3">
    `;

    // Iterate object key-value pairs
    for (const [name, description] of Object.entries(parsed.components)) {
        explanationHTML += `<li><strong>${name}:</strong> ${description}</li>`;
    }

    explanationHTML += `</ul>`;
    explanationHTML += `<h5 class="font-semibold mt-3">Interpretation:</h5><p>${parsed.interpretation}</p>`;

    explanation.innerHTML = explanationHTML;
} catch (error) {
    explanation.innerHTML = `<pre>${JSON.stringify(data.explanation, null, 2)}</pre>`;
}

                    resultsDiv.classList.remove("hidden");

                    // Draw chart
                    new Chart(chartCanvas, {
                        type: "bar",
                        data: {
                            labels: labels,
                            datasets: [{
                                label: formId.includes("wireless") ? "Data Rate (Mbps)" : "Value",
                                data: values,
                                backgroundColor: ["#36A2EB", "#FF6384", "#4BC0C0", "#FFCE56", "#E7E9ED", "#9966FF"],
                                borderColor: ["#2A8CC7", "#D84A6A", "#3AA0A0", "#D4A437", "#C7C9CB", "#7A52CC"],
                                borderWidth: 1
                            }]
                        },
                        options: {
                            scales: {
                                y: {
                                    beginAtZero: true,
                                    title: {
                                        display: true,
                                        text: formId.includes("wireless") ? "Data Rate (Mbps)" : "Value"
                                    }
                                },
                                x: {
                                    title: {
                                        display: true,
                                        text: "Metric"
                                    }
                                }
                            }
                        }
                    });
                } else {
                    const error = await response.json();
                    alert(error.error || "Something went wrong.");
                }
            });
        }
    });
});
