/* docs/assets/javascripts/scroll_header.js */

const setupHeader = () => {
    const hero = document.querySelector(".oscar-hero");
    const header = document.querySelector(".md-header");
    const tabs = document.querySelector(".md-tabs");
    const body = document.querySelector("body");

    // the stuff we want to fade out when scrolling down
    const heroContent = document.querySelectorAll(
        ".hero-logo-container, .hero-buttons, .hero-badges"
    );

    if (hero) {
        body.classList.add("oscar-homepage");

        const updateOnScroll = () => {
            const scrollY = window.scrollY;
            const heroHeight = hero.offsetHeight;

            // 1. toggle solid blue header when hero section is mostly gone
            // (hero height minus ~64px header + padding)
            const headerThreshold = heroHeight - 120;

            if (scrollY > headerThreshold) {
                header.classList.add("header-scrolled");
                if (tabs) tabs.classList.add("header-scrolled");
            } else {
                header.classList.remove("header-scrolled");
                if (tabs) tabs.classList.remove("header-scrolled");
            }

            // 2. fade out hero elements so they don't clash with the scrolling content
            // fully invisible at 50% scroll
            const fadeLimit = heroHeight * 0.5;

            let opacity = 1 - (scrollY / fadeLimit);
            opacity = Math.max(0, Math.min(1, opacity));

            heroContent.forEach(el => {
                el.style.opacity = opacity;
                // prevent weird ghost clicks when invisible
                el.style.pointerEvents = opacity <= 0.1 ? 'none' : 'auto';
            });
        };

        // we need to clean up old listeners first or mkdocs instant loading will duplicate them
        window.removeEventListener("scroll", window._oscarScrollHandler);
        window.removeEventListener("resize", window._oscarScrollHandler);

        window._oscarScrollHandler = updateOnScroll;
        window.addEventListener("scroll", window._oscarScrollHandler);
        window.addEventListener("resize", window._oscarScrollHandler);

        // init
        updateOnScroll();

    } else {
        body.classList.remove("oscar-homepage");

        // reset everything on normal pages
        if (heroContent) {
            heroContent.forEach(el => {
                el.style.opacity = 1;
                el.style.pointerEvents = 'auto';
            });
        }
    }
};

// mkdocs material spa navigation hooks
document.addEventListener("DOMContentLoaded", setupHeader);

if (typeof document$.subscribe !== 'undefined') {
    document$.subscribe(setupHeader);
}

// set current year in footer
const yearEl = document.getElementById('year');
if (yearEl) yearEl.textContent = new Date().getFullYear();
