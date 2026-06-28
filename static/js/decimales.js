// Seleccionar los 3 inputs
const inputs = [
  document.getElementById("believe"),
  document.getElementById("comi"),
];

/**
 * Formatea un número con separador de miles (punto) y coma decimal
 * @param {number} numero - El número a formatear
 * @returns {string} Número formateado ej: "1.234,56"
 */
function formatearNumero(numero) {
  // Separar parte entera y decimal
  let [entero, decimal] = numero.toFixed(2).split(".");

  // Agregar separador de miles (punto) a la parte entera
  entero = entero.replace(/\B(?=(\d{3})+(?!\d))/g, ".");

  // Retornar con coma decimal
  return entero + "," + decimal;
}

/**
 * Procesa la entrada del usuario y formatea automáticamente
 * @param {Event} e - Evento del input
 * @param {HTMLElement} inputElement - El input que disparó el evento
 */
function procesarEntrada(e, inputElement) {
  // Obtener solo dígitos numéricos
  let soloDigitos = inputElement.value.replace(/[^0-9]/g, "");

  // Si está vacío, mostrar 0,00
  if (soloDigitos === "") {
    inputElement.value = "0,00";
    return;
  }

  // Convertir a número entero y dividir entre 100 (para 2 decimales)
  let numeroEntero = parseInt(soloDigitos, 10);
  let numeroConDecimales = numeroEntero / 100;

  // Formatear con miles y decimales
  let resultadoFormateado = formatearNumero(numeroConDecimales);

  // Asignar al input
  inputElement.value = resultadoFormateado;
}

/**
 * Asegura formato correcto cuando el input pierde el foco
 * @param {HTMLElement} inputElement
 */
function asegurarFormato(inputElement) {
  if (inputElement.value === "" || inputElement.value === "0,00") {
    inputElement.value = "0,00";
    return;
  }

  // Convertir formato europeo a número (eliminar puntos y cambiar coma por punto)
  let valorLimpio = inputElement.value.replace(/\./g, "").replace(",", ".");
  let numero = parseFloat(valorLimpio);

  if (isNaN(numero)) {
    inputElement.value = "0,00";
  } else {
    inputElement.value = formatearNumero(numero);
  }
}

/**
 * Coloca el cursor al final del texto
 * @param {HTMLElement} inputElement
 */
function cursorAlFinal(inputElement) {
  inputElement.setSelectionRange(
    inputElement.value.length,
    inputElement.value.length,
  );
}

// Aplicar los eventos a cada input
inputs.forEach((input) => {
  // Evento mientras se escribe
  input.addEventListener("input", (e) => procesarEntrada(e, input));

  // Evento al perder foco
  input.addEventListener("blur", () => asegurarFormato(input));

  // Evento al hacer foco (cursor al final)
  input.addEventListener("focus", () => cursorAlFinal(input));

  // Inicializar con 0,00
  input.value = "0,00";
});

/**
 * Función para reiniciar todos los inputs a 0,00
 */
function reiniciarTodos() {
  inputs.forEach((input) => {
    input.value = "0,00";
  });
}

// Exponer función global para el botón
window.reiniciarTodos = reiniciarTodos;

// Ejemplo adicional: Obtener valores numéricos reales de los inputs
function obtenerValorNumerico(inputElement) {
  let valorStr = inputElement.value;
  let valorLimpio = valorStr.replace(/\./g, "").replace(",", ".");
  return parseFloat(valorLimpio);
}

// Puedes usar esta función para cálculos (ejemplo en consola)
console.log("Script cargado - Los inputs formatean automáticamente");
