let headers = [];
let rows = [];
let columnasOcultas = [
    "Periodos Detallados",
    "Indeterminacion de contrato",
    "Dias para ser indeterminado",
    "Finalizacion de contrato",
    "Dias para terminar contrato"
];
let indicesOcultosOriginales = [];
let currentSort = { col: "Tiempo Servicio", asc: false };

async function cargarCSV() {
    const response = await fetch("contrato.csv", {
        headers: { 'Accept': 'text/csv; charset=utf-8' }
    });
    const text = await response.text();
    const lines = text.trim().split("\n").filter(line => line.trim() !== "");
    headers = lines[0].split(";").map(h => h.trim());
    rows = lines.slice(1).map(l => l.split(";").map(c => c.trim()));

    columnasOcultas.forEach(col => {
        const index = headers.indexOf(col);
        if (index !== -1) {
            indicesOcultosOriginales.push(index);
        }
    });

    // Ordenamos al revés para eliminar sin desfases
    indicesOcultosOriginales.sort((a, b) => b - a);
    indicesOcultosOriginales.forEach(i => headers.splice(i, 1));
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
            if (indicesOcultosOriginales.includes(i)) return;

            const colIndexAjustado = i - indicesOcultosOriginales.filter(x => x < i).length;
            const col = headers[colIndexAjustado];
            const td = document.createElement("td");
            td.setAttribute("data-col", col);

            if (col === "Periodos") {
                const indexDetalle = columnasOcultas.indexOf("Periodos Detallados");
                const indexRealDetalle = indexDetalle !== -1 ? indicesOcultosOriginales[indexDetalle] : -1;
                const detalleTexto = row[indexRealDetalle];

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
                    const periodosArray = detalleTexto?.split(" / ") ?? [];
                    document.getElementById("modalText").innerHTML =
                        "<ul style='padding-left: 20px;'>" +
                        periodosArray.map(p => `<li>${p.trim()}</li>`).join("") +
                        "</ul>";
                    document.getElementById("periodosModal").style.display = "block";
                });
            } else {
                td.textContent = celda;
            }

            tr.appendChild(td);
        });

        tbody.appendChild(tr);
    });
}

function actualizarFiltros(columna, selectorId) {
    const index = headers.indexOf(columna);
    const selector = document.getElementById(selectorId);
    const valores = [...new Set(rows.map(r => {
        const realIndex = headers.indexOf(columna);
        return r.filter((_, i) => !indicesOcultosOriginales.includes(i))[realIndex];
    }).filter(Boolean))].sort();

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
            const realIndex = row.findIndex((_, idx) => {
                const colIndexAjustado = idx - indicesOcultosOriginales.filter(x => x < idx).length;
                return headers[colIndexAjustado] === col;
            });
            return val === "" || row[realIndex] === val;
        }) && row.some((celda, i) => {
            if (indicesOcultosOriginales.includes(i)) return false;
            const colIndexAjustado = i - indicesOcultosOriginales.filter(x => x < i).length;
            const colName = headers[colIndexAjustado];
            return ["Nombre", "Dni", "Cargo", "Contrato"].includes(colName) && celda.toLowerCase().includes(termino);
        })
    );

    if (currentSort.col) {
        const index = headers.indexOf(currentSort.col);
        const esNumerico = ["Periodos", "Tiempo Servicio"].includes(currentSort.col);

        filtrados.sort((a, b) => {
            let valA = a.filter((_, i) => !indicesOcultosOriginales.includes(i))[index];
            let valB = b.filter((_, i) => !indicesOcultosOriginales.includes(i))[index];

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
    contenido += datos.map(row => {
        return row.filter((_, i) => !indicesOcultosOriginales.includes(i)).join(";");
    }).join("\n");

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