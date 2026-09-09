/*
    JavaScript de la vista "Solicita tu libro".
    Consulta el endpoint Open Library del backend, muestra resultados y
    reutiliza el formulario POST existente para crear la solicitud.
*/

document.addEventListener("DOMContentLoaded", () => {
    /* Referencias a los elementos interactivos de la vista. */
    const form = document.getElementById("openLibrarySearchForm");
    const queryInput = document.getElementById("openLibraryQuery");
    const searchButton = document.getElementById("openLibrarySearchButton");
    const searchUrl = form?.dataset.searchUrl || "";
    const status = document.getElementById("openLibraryStatus");
    const results = document.getElementById("openLibraryResults");
    const requestForm = document.getElementById("bookRequestForm");

    /* Campos ocultos que alimentan el backend actual. */
    const hiddenFields = {
        titulo: document.getElementById("requestTitulo"),
        autor: document.getElementById("requestAutor"),
        editorial: document.getElementById("requestEditorial"),
        anio: document.getElementById("requestAnio"),
        portada: document.getElementById("requestPortadaURL"),
        key: document.getElementById("requestOpenLibraryKey"),
    };

    /* Escapa texto para evitar insertar contenido externo como HTML activo. */
    const escapeHtml = (value) => {
        const div = document.createElement("div");
        div.textContent = value ?? "";
        return div.innerHTML;
    };

    /* Consulta el endpoint Django que encapsula Open Library. */
    const buscar = async (termino) => {
        if (!searchUrl) {
            throw new Error("No se configuró la URL de búsqueda de Open Library.");
        }

        const separator = searchUrl.includes("?") ? "&" : "?";
        const url = `${searchUrl}${separator}q=${encodeURIComponent(termino)}`;

        const response = await fetch(url, {
            method: "GET",
            headers: {
                "X-Requested-With": "XMLHttpRequest",
                "Accept": "application/json",
            },
        });

        if (!response.ok) {
            throw new Error("No fue posible consultar Open Library.");
        }

        return response.json();
    };

    /* Renderiza las tarjetas recibidas desde el backend. */
    const renderResults = (items) => {
        results.innerHTML = "";

        items.forEach((item) => {
            const card = document.createElement("article");
            card.className = "open-library-card";

            const cover = item.portada
                ? `<img src="${escapeHtml(item.portada)}" alt="Portada de ${escapeHtml(item.titulo)}" loading="lazy">`
                : `<div class="open-library-cover-empty"><i class="bi bi-book"></i></div>`;

            const author = escapeHtml(item.autor || "Autor no informado");
            const publisher = escapeHtml(item.editorial || "Editorial no informada");
            const year = escapeHtml(item.anio ? String(item.anio) : "Año no informado");
            const isbn = escapeHtml(item.isbn || "No disponible");

            card.innerHTML = `
                <div class="open-library-cover">${cover}</div>
                <div class="open-library-copy">
                    <span class="open-library-badge">OPEN LIBRARY</span>
                    <h3>${escapeHtml(item.titulo)}</h3>
                    <p><strong>Autor:</strong> ${author}</p>
                    <p><strong>Editorial:</strong> ${publisher}</p>
                    <p><strong>Publicación:</strong> ${year}</p>
                    <p><strong>ISBN:</strong> ${isbn}</p>
                    ${item.en_biblioteca
                        ? `<div class="open-library-local-state"><i class="bi bi-check-circle"></i> Este libro ya está en la biblioteca.</div>`
                        : `<button class="btn-ui btn-red open-library-request" type="button">
                            <i class="bi bi-send"></i> Solicitar este libro
                        </button>`
                    }
                </div>
            `;

            if (!item.en_biblioteca) {
                const button = card.querySelector(".open-library-request");
                button.addEventListener("click", () => {
                    /* Copiamos únicamente los datos seleccionados al POST. */
                    hiddenFields.titulo.value = item.titulo || "";
                    hiddenFields.autor.value = item.autor || "";
                    hiddenFields.editorial.value = item.editorial || "";
                    hiddenFields.anio.value = item.anio ? String(item.anio) : "";
                    hiddenFields.portada.value = item.portada || "";
                    hiddenFields.key.value = item.key || "";
                    requestForm.submit();
                });
            }

            results.appendChild(card);
        });
    };

    /* Manejo del formulario de búsqueda. */
    form.addEventListener("submit", async (event) => {
        event.preventDefault();

        const termino = queryInput.value.trim();

        if (!termino) {
            status.textContent = "Escribe el nombre de un libro para comenzar.";
            results.innerHTML = "";
            return;
        }

        status.textContent = "Buscando libros...";
        searchButton.disabled = true;
        results.innerHTML = "";

        try {
            const data = await buscar(termino);
            const items = Array.isArray(data.resultados) ? data.resultados : [];

            if (!items.length) {
                status.textContent = "No encontramos resultados. Prueba con otro título.";
                return;
            }

            status.textContent = `${items.length} resultado(s) encontrado(s).`;
            renderResults(items);
        } catch (error) {
            console.error(error);
            status.textContent = "No se pudo realizar la búsqueda. Inténtalo nuevamente.";
        } finally {
            searchButton.disabled = false;
        }
    });
});
