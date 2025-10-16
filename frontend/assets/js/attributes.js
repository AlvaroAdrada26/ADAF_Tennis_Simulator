function updateValueColor(slider, valueEl) {
  const val = parseInt(slider.value);
  let color = "";

  if (val < 60) color = "#ef4444"; // rojo
  else if (val < 80) color = "#fbbf24"; // amarillo
  else color = "#22c55e"; // verde

  // Transición suave de color 👇
  valueEl.style.transition = "color 0.3s ease";
  valueEl.style.color = color;
}


// Inicializa colores al cargar la página
document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".slider").forEach(slider => {
    const valueEl = slider.nextElementSibling;
    updateValueColor(slider, valueEl);
  });
});
