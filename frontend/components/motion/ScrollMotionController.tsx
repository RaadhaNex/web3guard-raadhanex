"use client";

import { useEffect } from "react";

const motionSelector = [
  ".cinematic-section",
  ".cinematic-page-hero",
  ".cinematic-panel",
  ".cinematic-card",
  ".cinematic-mini-card",
  ".clean-panel",
  ".surface-panel",
  ".card",
  ".home-glass-card",
  ".home-step-card",
  ".home-state-card",
  ".home-final-cta",
  ".scroll-story-card",
  ".scroll-story-sticky",
  "[data-scroll-motion]",
].join(",");

function toHTMLElement(element: Element): HTMLElement | null {
  return element instanceof HTMLElement ? element : null;
}

export function ScrollMotionController() {
  useEffect(() => {
    if (typeof window === "undefined") return;

    const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const root = document.documentElement;

    if (prefersReducedMotion) {
      root.classList.add("motion-reduced");
      return;
    }

    root.classList.add("motion-enhanced");

    const elements = Array.from(document.querySelectorAll(motionSelector))
      .map(toHTMLElement)
      .filter(Boolean) as HTMLElement[];

    elements.forEach((element, index) => {
      if (element.classList.contains("site-header")) return;
      element.classList.add("scroll-motion-ready");
      element.style.setProperty("--motion-delay", `${Math.min(index % 8, 7) * 55}ms`);
    });

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          const target = toHTMLElement(entry.target);
          if (!target) return;
          if (entry.isIntersecting) {
            target.classList.add("scroll-motion-visible");
          }
        });
      },
      { root: null, rootMargin: "0px 0px -12% 0px", threshold: 0.14 }
    );

    elements.forEach((element) => observer.observe(element));

    const parallaxElements = Array.from(document.querySelectorAll("[data-parallax]"))
      .map(toHTMLElement)
      .filter(Boolean) as HTMLElement[];

    let raf = 0;
    const updateScrollMotion = () => {
      raf = 0;
      const viewportHeight = window.innerHeight || 1;
      root.style.setProperty("--page-scroll-y", `${window.scrollY}`);

      parallaxElements.forEach((element) => {
        const speed = Number(element.dataset.parallax ?? "0.04");
        const rect = element.getBoundingClientRect();
        const distanceFromCenter = rect.top + rect.height / 2 - viewportHeight / 2;
        const y = Math.max(Math.min(distanceFromCenter * -speed, 72), -72);
        element.style.setProperty("--parallax-y", `${y.toFixed(2)}px`);
      });
    };

    const requestUpdate = () => {
      if (raf) return;
      raf = window.requestAnimationFrame(updateScrollMotion);
    };

    updateScrollMotion();
    window.addEventListener("scroll", requestUpdate, { passive: true });
    window.addEventListener("resize", requestUpdate);

    return () => {
      observer.disconnect();
      window.removeEventListener("scroll", requestUpdate);
      window.removeEventListener("resize", requestUpdate);
      if (raf) window.cancelAnimationFrame(raf);
    };
  }, []);

  return null;
}
