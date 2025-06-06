window.addEventListener("DOMContentLoaded", function () {
  function showSection(sectionId) {
    const sections = [
      "main-content",
      "descargas-content",
      "quienes-content",
      "contactar-content",
      "faq-content",
    ];
    sections.forEach((id) => {
      const elem = document.getElementById(id);
      if (elem) {
        if (id === sectionId) {
          elem.style.display = "block";
          // Aplica el efecto de fade in
          setTimeout(() => {
            elem.classList.remove("opacity-0");
            elem.classList.add("opacity-100");
            elem.classList.add("transition-opacity", "duration-500");
          }, 10);
        } else {
          elem.classList.add("opacity-0");
          elem.classList.remove("opacity-100");
          elem.style.display = "none";
        }
      }
    });
  }

  // Navegación de menú
  document.getElementById("nav-inicio").addEventListener("click", function (e) {
    e.preventDefault();
    showSection("main-content");
  });
  document
    .getElementById("nav-descargas")
    .addEventListener("click", function (e) {
      e.preventDefault();
      showSection("descargas-content");
    });
  document
    .getElementById("nav-quienes")
    .addEventListener("click", function (e) {
      e.preventDefault();
      showSection("quienes-content");
    });
  document
    .getElementById("nav-contactar")
    .addEventListener("click", function (e) {
      e.preventDefault();
      showSection("contactar-content");
    });
  document.getElementById("nav-faq").addEventListener("click", function (e) {
    e.preventDefault();
    showSection("faq-content");
  });

  // FAQ Acordeón con fade
  document.querySelectorAll(".faq-question").forEach((btn) => {
    btn.addEventListener("click", function () {
      const answer = this.parentElement.querySelector(".faq-answer");
      const wasOpen = !answer.classList.contains("hidden"); // Verifica si ya estaba abierto

      // Cierra todas las respuestas
      document.querySelectorAll(".faq-answer").forEach((ans) => {
        ans.classList.add("hidden");
        ans.classList.add("opacity-0");
        ans.classList.remove("opacity-100");
      });
      document
        .querySelectorAll(".faq-question span")
        .forEach((icon) => (icon.textContent = "+"));

      // Si no estaba abierto, lo abre
      if (!wasOpen) {
        answer.classList.remove("hidden");
        setTimeout(() => {
          answer.classList.remove("opacity-0");
          answer.classList.add("opacity-100");
        }, 10);
        this.querySelector("span").textContent = "–";
      }
    });
  });
  // Botón de modo oscuro
  const darkModeToggle = document.getElementById("darkModeToggle");
  const htmlEl = document.documentElement;

  if (darkModeToggle) {
    const updateToggleButton = () => {
      if (htmlEl.classList.contains("dark")) {
        darkModeToggle.innerHTML = "☀️";
      } else {
        darkModeToggle.innerHTML = "🌙";
      }
    };

    if (
      localStorage.getItem("theme") === "dark" ||
      (!("theme" in localStorage) &&
        window.matchMedia("(prefers-color-scheme: dark)").matches)
    ) {
      htmlEl.classList.add("dark");
    }
    updateToggleButton();

    darkModeToggle.addEventListener("click", () => {
      htmlEl.classList.toggle("dark");
      if (htmlEl.classList.contains("dark")) {
        localStorage.setItem("theme", "dark");
      } else {
        localStorage.setItem("theme", "light");
      }
      updateToggleButton();
    });
  }

  // Mostrar solo la sección de inicio al cargar
  showSection("main-content");

  // Testimonial Carousel with Drag and Autoscroll
  function setupTestimonialCarousel() {
    const carousel = document.getElementById("testimonial-carousel");
    if (!carousel) return;

    let isDown = false;
    const scrollSpeed = 1;

    const animationStep = () => {
      const contentWidth = carousel.scrollWidth / 2;

      // Autoscroll if not dragging
      if (!isDown) {
        carousel.scrollLeft += scrollSpeed;
      }

      // Infinite loop check
      if (contentWidth > 0) {
        if (carousel.scrollLeft >= contentWidth) {
          carousel.scrollLeft -= contentWidth;
        } else if (carousel.scrollLeft <= 0) {
          // When starting or scrolling to the left end, jump to the same position in the duplicated content
          carousel.scrollLeft += contentWidth;
        }
      }

      requestAnimationFrame(animationStep);
    };

    carousel.addEventListener("mousedown", (e) => {
      isDown = true;
      carousel.classList.add("cursor-grabbing");
      carousel.classList.remove("cursor-grab");
    });

    carousel.addEventListener("mouseleave", () => {
      isDown = false;
      carousel.classList.remove("cursor-grabbing");
      carousel.classList.add("cursor-grab");
    });

    // Use a global mouseup to avoid getting stuck in a dragging state
    window.addEventListener("mouseup", () => {
      if (isDown) {
        isDown = false;
        carousel.classList.remove("cursor-grabbing");
        carousel.classList.add("cursor-grab");
      }
    });

    carousel.addEventListener("mousemove", (e) => {
      if (!isDown) return;
      e.preventDefault();
      carousel.scrollLeft -= e.movementX;
    });

    // Start the animation loop
    requestAnimationFrame(animationStep);
  }
  setupTestimonialCarousel();
});
