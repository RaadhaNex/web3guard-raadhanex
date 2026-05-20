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

function asHtmlElement(element: Element): HTMLElement | null {
  return element instanceof HTMLElement ? element : null;
}

export function ScrollMotionController() {
  useEffect(() => {
    if (typeof window === "undefined") return;

    const root = document.documentElement;
    const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    if (prefersReducedMotion) {
      root.classList.add("motion-reduced");
      root.classList.remove("motion-enhanced");
      return;
    }

    root.classList.add("motion-enhanced");

    const collectElements = () =>
      Array.from(document.querySelectorAll(motionSelector))
        .map(asHtmlElement)
        .filter(Boolean) as HTMLElement[];

    const revealImmediately = (elements: HTMLElement[]) => {
      elements.forEach((element, index) => {
        if (element.classList.contains("site-header")) return;
        element.classList.add("scroll-motion-ready");
        element.style.setProperty("--motion-delay", `${Math.min(index % 8, 7) * 45}ms`);

        const rect = element.getBoundingClientRect();
        const isNearViewport = rect.top < window.innerHeight * 1.35;
        if (isNearViewport) {
          element.classList.add("scroll-motion-visible");
        }
      });
    };

    let elements = collectElements();
    revealImmediately(elements);

    const safeRevealTimer = window.setTimeout(() => {
      collectElements().forEach((element) => element.classList.add("scroll-motion-visible"));
    }, 900);

    if (!("IntersectionObserver" in window)) {
      collectElements().forEach((element) => element.classList.add("scroll-motion-visible"));
      return () => window.clearTimeout(safeRevealTimer);
    }

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          const target = asHtmlElement(entry.target);
          if (!target) return;
          if (entry.isIntersecting) {
            target.classList.add("scroll-motion-visible");
          }
        });
      },
      { root: null, rootMargin: "0px 0px -6% 0px", threshold: 0.04 }
    );

    elements.forEach((element) => observer.observe(element));

    const mutationObserver = new MutationObserver(() => {
      elements = collectElements();
      revealImmediately(elements);
      elements.forEach((element) => observer.observe(element));
    });

    mutationObserver.observe(document.body, { childList: true, subtree: true });

    const parallaxElements = Array.from(document.querySelectorAll("[data-parallax]"))
      .map(asHtmlElement)
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
      window.clearTimeout(safeRevealTimer);
      observer.disconnect();
      mutationObserver.disconnect();
      window.removeEventListener("scroll", requestUpdate);
      window.removeEventListener("resize", requestUpdate);
      if (raf) window.cancelAnimationFrame(raf);
    };
  }, []);

  return null;
}
