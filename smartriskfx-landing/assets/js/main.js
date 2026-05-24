/* ============================================
   SMART RISK FX - MAIN JAVASCRIPT
   Professional Marketing Landing Page
   ============================================ */

(function() {
    'use strict';

    // ============================================
    // DOM READY
    // ============================================
    document.addEventListener('DOMContentLoaded', function() {
        initNavbar();
        initScrollAnimations();
        initCounterAnimations();
        initBackToTop();
        initSmoothScroll();
        initMobileMenu();
        initLiveTicker();
        initParallax();
        initTypingEffect();
        initMagneticButtons();
    });

    // ============================================
    // NAVBAR SCROLL EFFECT
    // ============================================
    function initNavbar() {
        const navbar = document.getElementById('navbar');
        if (!navbar) return;

        let lastScroll = 0;

        window.addEventListener('scroll', function() {
            const currentScroll = window.pageYOffset;

            // Add/remove scrolled class
            if (currentScroll > 50) {
                navbar.classList.add('scrolled');
            } else {
                navbar.classList.remove('scrolled');
            }

            // Hide/show navbar on scroll direction
            if (currentScroll > lastScroll && currentScroll > 100) {
                navbar.style.transform = 'translateY(-100%)';
            } else {
                navbar.style.transform = 'translateY(0)';
            }

            lastScroll = currentScroll;
        }, { passive: true });
    }

    // ============================================
    // SCROLL ANIMATIONS (AOS-like)
    // ============================================
    function initScrollAnimations() {
        const animatedElements = document.querySelectorAll('[data-aos]');

        if (!animatedElements.length) return;

        const observerOptions = {
            root: null,
            rootMargin: '0px 0px -50px 0px',
            threshold: 0.1
        };

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('aos-animate');
                    observer.unobserve(entry.target);
                }
            });
        }, observerOptions);

        animatedElements.forEach(el => observer.observe(el));
    }

    // ============================================
    // COUNTER ANIMATIONS
    // ============================================
    function initCounterAnimations() {
        const counters = document.querySelectorAll('[data-count]');

        if (!counters.length) return;

        const observerOptions = {
            threshold: 0.5
        };

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const target = entry.target;
                    const countTo = parseInt(target.getAttribute('data-count'));
                    animateCounter(target, countTo);
                    observer.unobserve(target);
                }
            });
        }, observerOptions);

        counters.forEach(counter => observer.observe(counter));
    }

    function animateCounter(element, target) {
        const duration = 2000;
        const start = 0;
        const startTime = performance.now();

        function update(currentTime) {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);

            // Easing function (easeOutQuart)
            const easeProgress = 1 - Math.pow(1 - progress, 4);
            const current = Math.floor(start + (target - start) * easeProgress);

            element.textContent = current.toLocaleString();

            if (progress < 1) {
                requestAnimationFrame(update);
            } else {
                element.textContent = target.toLocaleString();
            }
        }

        requestAnimationFrame(update);
    }

    // ============================================
    // BACK TO TOP BUTTON
    // ============================================
    function initBackToTop() {
        const backToTop = document.getElementById('backToTop');
        if (!backToTop) return;

        window.addEventListener('scroll', function() {
            if (window.pageYOffset > 500) {
                backToTop.classList.add('visible');
            } else {
                backToTop.classList.remove('visible');
            }
        }, { passive: true });

        backToTop.addEventListener('click', function() {
            window.scrollTo({
                top: 0,
                behavior: 'smooth'
            });
        });
    }

    // ============================================
    // SMOOTH SCROLL FOR ANCHOR LINKS
    // ============================================
    function initSmoothScroll() {
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function(e) {
                const href = this.getAttribute('href');
                if (href === '#') return;

                const target = document.querySelector(href);
                if (target) {
                    e.preventDefault();
                    const navHeight = document.getElementById('navbar').offsetHeight;
                    const targetPosition = target.getBoundingClientRect().top + window.pageYOffset - navHeight - 20;

                    window.scrollTo({
                        top: targetPosition,
                        behavior: 'smooth'
                    });
                }
            });
        });
    }

    // ============================================
    // MOBILE MENU
    // ============================================
    function initMobileMenu() {
        const toggle = document.getElementById('mobileToggle');
        const menu = document.getElementById('navMenu');

        if (!toggle || !menu) return;

        toggle.addEventListener('click', function() {
            this.classList.toggle('active');
            menu.classList.toggle('active');
            document.body.style.overflow = menu.classList.contains('active') ? 'hidden' : '';
        });

        // Close menu when clicking a link
        menu.querySelectorAll('a').forEach(link => {
            link.addEventListener('click', () => {
                toggle.classList.remove('active');
                menu.classList.remove('active');
                document.body.style.overflow = '';
            });
        });

        // Close menu when clicking outside
        document.addEventListener('click', function(e) {
            if (!toggle.contains(e.target) && !menu.contains(e.target)) {
                toggle.classList.remove('active');
                menu.classList.remove('active');
                document.body.style.overflow = '';
            }
        });
    }

    // ============================================
    // LIVE TICKER ENHANCEMENTS
    // ============================================
    function initLiveTicker() {
        const ticker = document.querySelector('.ticker-track');
        if (!ticker) return;

        // Pause on hover
        ticker.addEventListener('mouseenter', () => {
            ticker.style.animationPlayState = 'paused';
        });

        ticker.addEventListener('mouseleave', () => {
            ticker.style.animationPlayState = 'running';
        });

        // Simulate price updates
        simulatePriceUpdates();
    }

    function simulatePriceUpdates() {
        const prices = document.querySelectorAll('.ticker-item .price-up, .ticker-item .price-down');

        setInterval(() => {
            prices.forEach(price => {
                const isUp = price.classList.contains('price-up');
                const randomChange = (Math.random() - 0.5) * 0.5;

                if (randomChange > 0.1) {
                    price.classList.remove('price-down');
                    price.classList.add('price-up');
                } else if (randomChange < -0.1) {
                    price.classList.remove('price-up');
                    price.classList.add('price-down');
                }
            });
        }, 5000);
    }

    // ============================================
    // PARALLAX EFFECT
    // ============================================
    function initParallax() {
        const orbs = document.querySelectorAll('.gradient-orb');
        if (!orbs.length) return;

        window.addEventListener('scroll', function() {
            const scrolled = window.pageYOffset;

            orbs.forEach((orb, index) => {
                const speed = 0.2 + (index * 0.1);
                const yPos = -(scrolled * speed);
                orb.style.transform = `translateY(${yPos}px)`;
            });
        }, { passive: true });
    }

    // ============================================
    // TYPING EFFECT (Optional enhancement)
    // ============================================
    function initTypingEffect() {
        const typingElements = document.querySelectorAll('.typing-effect');

        typingElements.forEach(el => {
            const text = el.textContent;
            el.textContent = '';
            el.classList.add('typing-cursor');

            let i = 0;
            const typeInterval = setInterval(() => {
                if (i < text.length) {
                    el.textContent += text.charAt(i);
                    i++;
                } else {
                    clearInterval(typeInterval);
                    el.classList.remove('typing-cursor');
                }
            }, 100);
        });
    }

    // ============================================
    // MAGNETIC BUTTON EFFECT
    // ============================================
    function initMagneticButtons() {
        const magneticBtns = document.querySelectorAll('.magnetic-btn, .btn-primary, .btn-secondary');

        // Only on non-touch devices
        if (window.matchMedia('(pointer: coarse)').matches) return;

        magneticBtns.forEach(btn => {
            btn.addEventListener('mousemove', function(e) {
                const rect = this.getBoundingClientRect();
                const x = e.clientX - rect.left - rect.width / 2;
                const y = e.clientY - rect.top - rect.height / 2;

                this.style.transform = `translate(${x * 0.2}px, ${y * 0.2}px)`;
            });

            btn.addEventListener('mouseleave', function() {
                this.style.transform = '';
            });
        });
    }

    // ============================================
    // SCROLL PROGRESS INDICATOR
    // ============================================
    function initScrollProgress() {
        const progressBar = document.createElement('div');
        progressBar.className = 'scroll-progress';
        progressBar.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            height: 3px;
            background: linear-gradient(90deg, #00D4FF, #7B61FF);
            z-index: 1001;
            transition: width 0.1s linear;
            width: 0%;
        `;
        document.body.appendChild(progressBar);

        window.addEventListener('scroll', function() {
            const scrollTop = window.pageYOffset;
            const docHeight = document.documentElement.scrollHeight - window.innerHeight;
            const progress = (scrollTop / docHeight) * 100;
            progressBar.style.width = progress + '%';
        }, { passive: true });
    }

    // Initialize scroll progress
    initScrollProgress();

    // ============================================
    // LAZY LOADING IMAGES
    // ============================================
    function initLazyLoading() {
        const lazyImages = document.querySelectorAll('img[data-src]');

        if (!lazyImages.length) return;

        const imageObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    img.src = img.dataset.src;
                    img.removeAttribute('data-src');
                    imageObserver.unobserve(img);
                }
            });
        });

        lazyImages.forEach(img => imageObserver.observe(img));
    }

    initLazyLoading();

    // ============================================
    // FORM VALIDATION (if forms are added later)
    // ============================================
    function validateEmail(email) {
        const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return re.test(email);
    }

    // ============================================
    // DEBOUNCE UTILITY
    // ============================================
    function debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    // ============================================
    // THROTTLE UTILITY
    // ============================================
    function throttle(func, limit) {
        let inThrottle;
        return function(...args) {
            if (!inThrottle) {
                func.apply(this, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    }

    // ============================================
    // PERFORMANCE MONITORING
    // ============================================
    if ('PerformanceObserver' in window) {
        const perfObserver = new PerformanceObserver((list) => {
            for (const entry of list.getEntries()) {
                if (entry.entryType === 'largest-contentful-paint') {
                    console.log('LCP:', entry.startTime);
                }
                if (entry.entryType === 'first-input') {
                    console.log('FID:', entry.processingStart - entry.startTime);
                }
            }
        });

        try {
            perfObserver.observe({ entryTypes: ['largest-contentful-paint', 'first-input'] });
        } catch (e) {
            // Fallback for older browsers
        }
    }


    // ============================================
    // VIDEO PLAYER FUNCTIONALITY
    // ============================================
    initVideoPlayer();

function initVideoPlayer() {
    const videoContainer = document.getElementById('videoContainer');
    const videoOverlay = document.getElementById('videoOverlay');
    const youtubeVideo = document.getElementById('youtubeVideo');

    if (!videoContainer || !videoOverlay || !youtubeVideo) return;

    let isPlaying = false;
    let clickCount = 0;

    videoOverlay.addEventListener('click', function() {
        clickCount++;

        if (clickCount === 1) {
            // First click - start playing
            isPlaying = true;
            videoOverlay.classList.add('hidden');
            videoContainer.classList.add('playing');

            // Send play command to YouTube iframe
            youtubeVideo.contentWindow.postMessage('{"event":"command","func":"playVideo","args":""}', '*');

        } else if (clickCount === 2) {
            // Second click - redirect to YouTube with autoplay
            window.open('https://www.youtube.com/watch?v=xKoD-CWqXdU&autoplay=1', '_blank');
        }
    });

    // Also handle clicks on the video container when overlay is hidden
    videoContainer.addEventListener('click', function(e) {
        if (isPlaying && clickCount >= 1) {
            // Increment click count when clicking on playing video
            clickCount++;
            if (clickCount >= 3) {
                window.open('https://www.youtube.com/watch?v=xKoD-CWqXdU&autoplay=1', '_blank');
            }
        }
    });
}

    // ============================================
    // CONSOLE BRANDING
    // ============================================
    console.log('%c SmartRisk FX ', 'background: linear-gradient(135deg, #00D4FF, #7B61FF); color: #0A0E1A; font-size: 24px; font-weight: bold; padding: 10px 20px; border-radius: 8px;');
    console.log('%c Professional AI-Powered Crypto Trading Signals ', 'color: #00D4FF; font-size: 14px;');
    console.log('%c https://smartriskfx.com ', 'color: #7B61FF; font-size: 12px;');

})();
