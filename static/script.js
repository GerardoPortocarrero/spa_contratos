let headers = [];
let rows = [];
let indexPeriodosDetallados = -1;
let currentSort = { col: "Tiempo Servicio", asc: false };

async function cargarCSV() {
    const response = await fetch("contrato.csv", {
        headers: { 'Accept': 'text/csv; charset=utf-8' }
    });
    const text = await response.text();
    const lines = text.trim().split("\n").filter(line => line.trim() !== "");
    headers = lines[0].split(";").map(h => h.trim());
    rows = lines.slice(1).map(l => l.split(";").map(c => c.trim()));

    indexPeriodosDetallados = headers.indexOf("Periodos Detallados");

    if (indexPeriodosDetallados !== -1) {
        headers.splice(indexPeriodosDetallados, 1); // Ocultamos esa columna
    }
}

function renderTabla(datos) {
    const thead = document.querySelector("#data-table thead");
    const tbody = document.querySelector("#data-table tbody");

    thead.innerHTML = "<tr>" + headers.map(h => {
        let icon = currentSort.col === h ? (currentSort.asc ? " ▲" : " ▼") : "";
        return `<th data-col="${h}" style="cursor:pointer" onclick="ordenarPor('${h}')">${h}${icon}</th>`;
    }).join("") + "</tr>";

    tbody.innerHTML = "";

    datos.forEach(row => {
        const tr = document.createElement("tr");

        row.forEach((celda, i) => {
            if (i === indexPeriodosDetallados) return; // omitimos la celda visualmente

            const col = headers[i >= indexPeriodosDetallados ? i - 1 : i]; // ajustar índice si ya quitamos una columna
            const td = document.createElement("td");

            td.textContent = celda;
            td.setAttribute("data-col", col);

            if (col === "Periodos" && indexPeriodosDetallados !== -1) {
                const detalleTexto = row[indexPeriodosDetallados];

                // Crear contenido visual con ícono y tooltip
                td.innerHTML = `
                    <span title="Haz clic para ver los periodos detallados" style="
                        cursor: pointer;
                        color: #007bff;
                        text-decoration: underline dotted;
                        display: inline-flex;
                        align-items: center;
                        gap: 4px;
                    ">
                        ${celda}
                        <span style="font-size: 14px; color: #007bff;">📅</span>
                    </span>
                `;

                td.addEventListener("click", () => {
                    const periodosArray = detalleTexto.split(" / ");
                    document.getElementById("modalText").innerHTML =
                        "<ul style='padding-left: 20px;'>" +
                        periodosArray.map(p => `<li>${p.trim()}</li>`).join("") +
                        "</ul>";
                    document.getElementById("periodosModal").style.display = "block";
                });
            }


            tr.appendChild(td);
        });

        tbody.appendChild(tr);
    });
}

function actualizarFiltros(columna, selectorId) {
    const index = headers.indexOf(columna);
    const selector = document.getElementById(selectorId);
    const valores = [...new Set(rows.map(r => r[index]).filter(Boolean))].sort();
    for (const val of valores) {
        const opt = document.createElement("option");
        opt.value = val;
        opt.textContent = val;
        selector.appendChild(opt);
    }
}

function aplicarFiltros() {
    const termino = document.getElementById("search").value.toLowerCase();
    const filtros = {
        "Locacion": document.getElementById("locacionFilter").value,
        "Cargo": document.getElementById("cargoFilter").value,
        "Contrato": document.getElementById("contratoFilter").value,
    };

    let filtrados = rows.filter(row =>
        Object.entries(filtros).every(([col, val]) => {
            const i = headers.indexOf(col);
            return val === "" || row[i] === val;
        }) && row.some((celda, i) => {
            const colName = headers[i >= indexPeriodosDetallados ? i - 1 : i];
            return ["Nombre", "Dni", "Cargo", "Contrato"].includes(colName) && celda.toLowerCase().includes(termino);
        })
    );

    if (currentSort.col) {
        const index = headers.indexOf(currentSort.col);
        const esNumerico = ["Periodos", "Tiempo Servicio"].includes(currentSort.col);

        filtrados.sort((a, b) => {
            let valA = a[index];
            let valB = b[index];
            if (esNumerico) {
                valA = parseFloat(valA.replace(",", ".")) || 0;
                valB = parseFloat(valB.replace(",", ".")) || 0;
            } else {
                valA = valA.toLowerCase();
                valB = valB.toLowerCase();
            }
            if (valA < valB) return currentSort.asc ? -1 : 1;
            if (valA > valB) return currentSort.asc ? 1 : -1;
            return 0;
        });
    }

    return filtrados;
}

function ordenarPor(columna) {
    if (currentSort.col === columna) {
        currentSort.asc = !currentSort.asc;
    } else {
        currentSort = { col: columna, asc: true };
    }
    renderTabla(aplicarFiltros());
}

function descargarCSV() {
    const datos = aplicarFiltros();
    let contenido = "\ufeff" + headers.join(";") + "\n";

    contenido += datos.map(row => row.join(";")).join("\n"); // ✅ sin eliminar columnas

    const blob = new Blob([contenido], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);

    const link = document.createElement("a");
    link.setAttribute("href", url);
    link.setAttribute("download", "contratos_filtrados.csv");
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

document.addEventListener("DOMContentLoaded", async () => {
    await cargarCSV();

    renderTabla(aplicarFiltros());

    actualizarFiltros("Locacion", "locacionFilter");
    actualizarFiltros("Cargo", "cargoFilter");
    actualizarFiltros("Contrato", "contratoFilter");

    document.getElementById("search").addEventListener("input", () => {
        renderTabla(aplicarFiltros());
    });

    ["locacionFilter", "cargoFilter", "contratoFilter"].forEach(id => {
        document.getElementById(id).addEventListener("change", () => {
            renderTabla(aplicarFiltros());
        });
    });
});

// Cerrar modal al hacer clic en la X
document.querySelector(".modal .close").onclick = function () {
    document.getElementById("periodosModal").style.display = "none";
};

// Cerrar modal si haces clic fuera del contenido
window.onclick = function (event) {
    const modal = document.getElementById("periodosModal");
    if (event.target === modal) {
        modal.style.display = "none";
    }
};
