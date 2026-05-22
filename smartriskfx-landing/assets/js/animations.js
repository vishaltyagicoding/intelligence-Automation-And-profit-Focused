/* ============================================
   SMART RISK FX - ANIMATIONS JAVASCRIPT
   Advanced Interactions & Effects
   ============================================ */

(function() {
    'use strict';

    document.addEventListener('DOMContentLoaded', function() {
        initParticleBackground();
        initMouseTrail();
        initTextScramble();
        initGlitchEffect();
        initWaveAnimation();
        init3DCardTilt();
        initScrollVelocity();
        initRevealOnScroll();
    });

    // ============================================
    // PARTICLE BACKGROUND (Canvas)
    // ============================================
    function initParticleBackground() {
        const canvas = document.createElement('canvas');
        canvas.id = 'particleCanvas';
        canvas.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
            z-index: 0;
            opacity: 0.3;
        `;

        // Only add to hero section
        const hero = document.querySelector('.hero');
        if (!hero) return;

        hero.insertBefore(canvas, hero.firstChild);

        const ctx = canvas.getContext('2d');
        let particles = [];
        const particleCount = 50;
        const connectionDistance = 150;
        const mouseDistance = 200;

        let mouse = { x: null, y: null };

        function resize() {
            canvas.width = window.innerWidth;
            canvas.height = window.innerHeight;
        }

        function createParticles() {
            particles = [];
            for (let i = 0; i < particleCount; i++) {
                particles.push({
                    x: Math.random() * canvas.width,
                    y: Math.random() * canvas.height,
                    vx: (Math.random() - 0.5) * 0.5,
                    vy: (Math.random() - 0.5) * 0.5,
                    size: Math.random() * 2 + 1,
                    color: Math.random() > 0.5 ? '#00D4FF' : '#7B61FF'
                });
            }
        }

        function drawParticles() {
            ctx.clearRect(0, 0, canvas.width, canvas.height);

            particles.forEach((particle, i) => {
                // Update position
                particle.x += particle.vx;
                particle.y += particle.vy;

                // Wrap around
                if (particle.x < 0) particle.x = canvas.width;
                if (particle.x > canvas.width) particle.x = 0;
                if (particle.y < 0) particle.y = canvas.height;
                if (particle.y > canvas.height) particle.y = 0;

                // Mouse interaction
                if (mouse.x !== null && mouse.y !== null) {
                    const dx = mouse.x - particle.x;
                    const dy = mouse.y - particle.y;
                    const distance = Math.sqrt(dx * dx + dy * dy);

                    if (distance < mouseDistance) {
                        const force = (mouseDistance - distance) / mouseDistance;
                        particle.vx += dx * force * 0.01;
                        particle.vy += dy * force * 0.01;
                    }
                }

                // Draw particle
                ctx.beginPath();
                ctx.arc(particle.x, particle.y, particle.size, 0, Math.PI * 2);
                ctx.fillStyle = particle.color;
                ctx.fill();

                // Draw connections
                for (let j = i + 1; j < particles.length; j++) {
                    const dx = particles[j].x - particle.x;
                    const dy = particles[j].y - particle.y;
                    const distance = Math.sqrt(dx * dx + dy * dy);

                    if (distance < connectionDistance) {
                        ctx.beginPath();
                        ctx.moveTo(particle.x, particle.y);
                        ctx.lineTo(particles[j].x, particles[j].y);
                        ctx.strokeStyle = `rgba(0, 212, 255, ${0.2 * (1 - distance / connectionDistance)})`;
                        ctx.lineWidth = 0.5;
                        ctx.stroke();
                    }
                }
            });

            requestAnimationFrame(drawParticles);
        }

        // Event listeners
        window.addEventListener('resize', () => {
            resize();
            createParticles();
        });

        hero.addEventListener('mousemove', (e) => {
            mouse.x = e.clientX;
            mouse.y = e.clientY;
        });

        hero.addEventListener('mouseleave', () => {
            mouse.x = null;
            mouse.y = null;
        });

        // Initialize
        resize();
        createParticles();
        drawParticles();
    }

    // ============================================
    // MOUSE TRAIL EFFECT
    // ============================================
    function initMouseTrail() {
        // Skip on touch devices
        if (window.matchMedia('(pointer: coarse)').matches) return;

        const trail = document.createElement('div');
        trail.className = 'mouse-trail';
        trail.style.cssText = `
            position: fixed;
            width: 20px;
            height: 20px;
            border-radius: 50%;
            background: radial-gradient(circle, rgba(0, 212, 255, 0.3), transparent);
            pointer-events: none;
            z-index: 9999;
            transition: transform 0.1s ease;
            mix-blend-mode: screen;
        `;
        document.body.appendChild(trail);

        let mouseX = 0, mouseY = 0;
        let trailX = 0, trailY = 0;

        document.addEventListener('mousemove', (e) => {
            mouseX = e.clientX;
            mouseY = e.clientY;
        });

        function animateTrail() {
            trailX += (mouseX - trailX) * 0.1;
            trailY += (mouseY - trailY) * 0.1;

            trail.style.transform = `translate(${trailX - 10}px, ${trailY - 10}px)`;
            requestAnimationFrame(animateTrail);
        }

        animateTrail();
    }

    // ============================================
    // TEXT SCRAMBLE EFFECT
    // ============================================
    function initTextScramble() {
        const elements = document.querySelectorAll('.scramble-text');

        elements.forEach(el => {
            const originalText = el.textContent;
            const chars = '!<>-_\/[]{}—=+*^?#________';
            let frame = 0;
            let queue = [];

            for (let i = 0; i < originalText.length; i++) {
                queue.push({
                    from: chars[Math.floor(Math.random() * chars.length)],
                    to: originalText[i],
                    start: Math.floor(Math.random() * 40),
                    end: Math.floor(Math.random() * 40) + 40
                });
            }

            function update() {
                let output = '';
                let complete = 0;

                for (let i = 0; i < queue.length; i++) {
                    let { from, to, start, end } = queue[i];
                    let char = chars[Math.floor(Math.random() * chars.length)];

                    if (frame >= end) {
                        complete++;
                        output += to;
                    } else if (frame >= start) {
                        if (!char || Math.random() < 0.28) {
                            char = to;
                        }
                        output += char;
                    } else {
                        output += from;
                    }
                }

                el.textContent = output;

                if (complete === queue.length) {
                    return;
                } else {
                    frame++;
                    requestAnimationFrame(update);
                }
            }

            // Start when element is visible
            const observer = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        update();
                        observer.unobserve(el);
                    }
                });
            });

            observer.observe(el);
        });
    }

    // ============================================
    // GLITCH EFFECT
    // ============================================
    function initGlitchEffect() {
        const glitchElements = document.querySelectorAll('.glitch');

        glitchElements.forEach(el => {
            const text = el.textContent;
            el.setAttribute('data-text', text);

            setInterval(() => {
                el.classList.add('glitch-active');
                setTimeout(() => {
                    el.classList.remove('glitch-active');
                }, 200);
            }, 5000 + Math.random() * 5000);
        });
    }

    // ============================================
    // WAVE ANIMATION FOR TEXT
    // ============================================
    function initWaveAnimation() {
        const waveElements = document.querySelectorAll('.wave-text');

        waveElements.forEach(el => {
            const text = el.textContent;
            el.innerHTML = '';

            text.split('').forEach((char, i) => {
                const span = document.createElement('span');
                span.textContent = char === ' ' ? ' ' : char;
                span.style.display = 'inline-block';
                span.style.animation = `wave 2s ease-in-out infinite`;
                span.style.animationDelay = `${i * 0.05}s`;
                el.appendChild(span);
            });
        });
    }

    // ============================================
    // 3D CARD TILT EFFECT
    // ============================================
    function init3DCardTilt() {
        const cards = document.querySelectorAll('.feature-card, .pricing-card, .testimonial-card');

        // Skip on touch devices
        if (window.matchMedia('(pointer: coarse)').matches) return;

        cards.forEach(card => {
            card.addEventListener('mousemove', (e) => {
                const rect = card.getBoundingClientRect();
                const x = e.clientX - rect.left;
                const y = e.clientY - rect.top;

                const centerX = rect.width / 2;
                const centerY = rect.height / 2;

                const rotateX = (y - centerY) / 20;
                const rotateY = (centerX - x) / 20;

                card.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) translateZ(10px)`;
                card.style.transition = 'transform 0.1s ease';
            });

            card.addEventListener('mouseleave', () => {
                card.style.transform = 'perspective(1000px) rotateX(0) rotateY(0) translateZ(0)';
                card.style.transition = 'transform 0.5s ease';
            });
        });
    }

    // ============================================
    // SCROLL VELOCITY EFFECT
    // ============================================
    function initScrollVelocity() {
        let lastScrollTop = 0;
        let velocity = 0;
        let ticking = false;

        const velocityElements = document.querySelectorAll('.velocity-sensitive');

        window.addEventListener('scroll', () => {
            if (!ticking) {
                requestAnimationFrame(() => {
                    const currentScrollTop = window.pageYOffset;
                    velocity = currentScrollTop - lastScrollTop;
                    lastScrollTop = currentScrollTop;

                    velocityElements.forEach(el => {
                        const skewAmount = Math.min(Math.max(velocity * 0.1, -5), 5);
                        el.style.transform = `skewY(${skewAmount}deg)`;
                    });

                    ticking = false;
                });

                ticking = true;
            }
        }, { passive: true });
    }

    // ============================================
    // REVEAL ON SCROLL (Enhanced)
    // ============================================
    function initRevealOnScroll() {
        const reveals = document.querySelectorAll('.reveal, .reveal-left, .reveal-right, .reveal-scale');

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('active');

                    // Add stagger to children if parent has stagger class
                    if (entry.target.classList.contains('stagger-children')) {
                        entry.target.classList.add('animate');
                    }

                    observer.unobserve(entry.target);
                }
            });
        }, {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        });

        reveals.forEach(el => observer.observe(el));
    }

    // ============================================
    // CUSTOM CURSOR
    // ============================================
    function initCustomCursor() {
        // Skip on touch devices
        if (window.matchMedia('(pointer: coarse)').matches) return;

        const cursor = document.createElement('div');
        cursor.className = 'custom-cursor';
        cursor.style.cssText = `
            position: fixed;
            width: 20px;
            height: 20px;
            border: 2px solid #00D4FF;
            border-radius: 50%;
            pointer-events: none;
            z-index: 10000;
            transition: transform 0.15s ease, width 0.2s ease, height 0.2s ease;
            transform: translate(-50%, -50%);
            mix-blend-mode: difference;
        `;

        const cursorDot = document.createElement('div');
        cursorDot.className = 'cursor-dot';
        cursorDot.style.cssText = `
            position: fixed;
            width: 4px;
            height: 4px;
            background: #00D4FF;
            border-radius: 50%;
            pointer-events: none;
            z-index: 10001;
            transform: translate(-50%, -50%);
        `;

        document.body.appendChild(cursor);
        document.body.appendChild(cursorDot);

        document.addEventListener('mousemove', (e) => {
            cursor.style.left = e.clientX + 'px';
            cursor.style.top = e.clientY + 'px';
            cursorDot.style.left = e.clientX + 'px';
            cursorDot.style.top = e.clientY + 'px';
        });

        // Hover effects
        const hoverElements = document.querySelectorAll('a, button, .feature-card, .pricing-card');

        hoverElements.forEach(el => {
            el.addEventListener('mouseenter', () => {
                cursor.style.width = '40px';
                cursor.style.height = '40px';
                cursor.style.borderColor = '#7B61FF';
            });

            el.addEventListener('mouseleave', () => {
                cursor.style.width = '20px';
                cursor.style.height = '20px';
                cursor.style.borderColor = '#00D4FF';
            });
        });
    }

    // Initialize custom cursor
    initCustomCursor();

    // ============================================
    // SMOOTH PARALLAX FOR IMAGES
    // ============================================
    function initImageParallax() {
        const parallaxImages = document.querySelectorAll('.parallax-img');

        window.addEventListener('scroll', () => {
            parallaxImages.forEach(img => {
                const rect = img.getBoundingClientRect();
                const scrolled = window.pageYOffset;
                const rate = scrolled * 0.3;

                if (rect.top < window.innerHeight && rect.bottom > 0) {
                    img.style.transform = `translateY(${rate}px)`;
                }
            });
        }, { passive: true });
    }

    initImageParallax();

    // ============================================
    // NUMBER COUNT UP WITH COMMAS
    // ============================================
    function animateNumber(element, target, duration = 2000) {
        const start = 0;
        const startTime = performance.now();

        function update(currentTime) {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);

            // Ease out quart
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
    // HORIZONTAL SCROLL SECTION
    // ============================================
    function initHorizontalScroll() {
        const horizontalSections = document.querySelectorAll('.horizontal-scroll');

        horizontalSections.forEach(section => {
            const container = section.querySelector('.horizontal-container');
            if (!container) return;

            section.addEventListener('wheel', (e) => {
                if (Math.abs(e.deltaY) > Math.abs(e.deltaX)) {
                    e.preventDefault();
                    container.scrollLeft += e.deltaY;
                }
            });
        });
    }

    initHorizontalScroll();

    // ============================================
    // AUDIO FEEDBACK (Optional)
    // ============================================
    function initAudioFeedback() {
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();

        function playHoverSound() {
            const oscillator = audioContext.createOscillator();
            const gainNode = audioContext.createGain();

            oscillator.connect(gainNode);
            gainNode.connect(audioContext.destination);

            oscillator.frequency.value = 800;
            oscillator.type = 'sine';

            gainNode.gain.setValueAtTime(0.02, audioContext.currentTime);
            gainNode.gain.exponentialRampToValueAtTime(0.001, audioContext.currentTime + 0.1);

            oscillator.start(audioContext.currentTime);
            oscillator.stop(audioContext.currentTime + 0.1);
        }

        // Add to buttons
        document.querySelectorAll('.btn-primary, .btn-secondary').forEach(btn => {
            btn.addEventListener('mouseenter', playHoverSound);
        });
    }

    // Uncomment to enable audio feedback
    // initAudioFeedback();

})();
