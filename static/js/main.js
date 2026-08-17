const menuButton = document.querySelector(".menu-toggle");
const nav = document.querySelector("#site-nav");
const themeButton = document.querySelector("[data-theme-toggle]");
const themeColor = document.querySelector('meta[name="theme-color"]');

function currentTheme() {
  return document.documentElement.getAttribute("data-theme") === "dark" ? "dark" : "light";
}

function syncThemeControl(theme) {
  if (!themeButton) {
    return;
  }
  const next = theme === "dark" ? "light" : "dark";
  themeButton.setAttribute("aria-pressed", String(theme === "dark"));
  const label = themeButton.querySelector("[data-theme-label]");
  if (label) {
    label.textContent = next === "dark" ? "Use dark theme" : "Use light theme";
  }
  if (themeColor) {
    themeColor.setAttribute("content", theme === "dark" ? "#121614" : "#f6f8f3");
  }
}

function setTheme(theme, persist) {
  document.documentElement.setAttribute("data-theme", theme);
  if (persist) {
    try {
      localStorage.setItem("asteria-theme", theme);
    } catch (error) {
      /* private mode */
    }
  }
  syncThemeControl(theme);
}

syncThemeControl(currentTheme());

if (themeButton) {
  themeButton.addEventListener("click", () => {
    setTheme(currentTheme() === "dark" ? "light" : "dark", true);
  });
}

try {
  if (!localStorage.getItem("asteria-theme") && window.matchMedia) {
    const media = window.matchMedia("(prefers-color-scheme: dark)");
    const onChange = (event) => setTheme(event.matches ? "dark" : "light", false);
    if (media.addEventListener) {
      media.addEventListener("change", onChange);
    }
  }
} catch (error) {
  /* ignore */
}

if (menuButton && nav) {
  menuButton.addEventListener("click", () => {
    const isOpen = document.body.classList.toggle("nav-open");
    menuButton.setAttribute("aria-expanded", String(isOpen));
    const label = menuButton.querySelector(".sr-only");
    if (label) {
      label.textContent = isOpen ? "Close navigation" : "Open navigation";
    }
  });

  nav.addEventListener("click", (event) => {
    if (event.target instanceof HTMLAnchorElement) {
      document.body.classList.remove("nav-open");
      menuButton.setAttribute("aria-expanded", "false");
      const label = menuButton.querySelector(".sr-only");
      if (label) {
        label.textContent = "Open navigation";
      }
    }
  });
}

const onScroll = () => {
  document.body.classList.toggle("is-scrolled", window.scrollY > 20);
};
onScroll();
window.addEventListener("scroll", onScroll, { passive: true });

function bindContactForm(contactForm) {
  const formStatus = contactForm.querySelector("[data-form-status]");
  if (!formStatus) {
    return;
  }

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

document.querySelectorAll("[data-contact-form]").forEach(bindContactForm);
