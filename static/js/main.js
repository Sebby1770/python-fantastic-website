const menuButton = document.querySelector(".menu-toggle");
const nav = document.querySelector("#site-nav");
const contactForm = document.querySelector("[data-contact-form]");
const formStatus = document.querySelector("[data-form-status]");

if (menuButton && nav) {
  menuButton.addEventListener("click", () => {
    const isOpen = document.body.classList.toggle("nav-open");
    menuButton.setAttribute("aria-expanded", String(isOpen));
  });

  nav.addEventListener("click", (event) => {
    if (event.target instanceof HTMLAnchorElement) {
      document.body.classList.remove("nav-open");
      menuButton.setAttribute("aria-expanded", "false");
    }
  });
}

if (contactForm && formStatus) {
  contactForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    formStatus.textContent = "";
    formStatus.classList.remove("is-error");

    const submitButton = contactForm.querySelector("button[type='submit']");
    if (submitButton) {
      submitButton.disabled = true;
    }

    try {
      const formData = new FormData(contactForm);
      const payload = Object.fromEntries(formData.entries());
      const response = await fetch("/contact", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.message || "Please check the form and try again.");
      }

      formStatus.textContent = data.message;
      contactForm.reset();
    } catch (error) {
      formStatus.classList.add("is-error");
      formStatus.textContent = error.message;
    } finally {
      if (submitButton) {
        submitButton.disabled = false;
      }
    }
  });
}
