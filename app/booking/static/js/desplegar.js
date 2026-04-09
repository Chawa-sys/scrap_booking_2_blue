document.addEventListener("DOMContentLoaded", function () {
    const botones = document.querySelectorAll(".toggle-detalle");

    botones.forEach(boton => {
        boton.addEventListener("click", function () {
            const id = this.getAttribute("data-id");
            const fila = document.getElementById(`detalle-${id}`);

            if (fila.style.display === "none") {
                fila.style.display = "table-row";
                this.textContent = "Ocultar";
            } else {
                fila.style.display = "none";
                this.textContent = "Ver más";
            }
        });
    });
});
