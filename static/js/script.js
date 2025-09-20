/*
=================================================================
    LAUNCHPAD.ORG - MAIN JAVASCRIPT FILE
=================================================================
*/

// Wait for the entire HTML document to be loaded and parsed
document.addEventListener('DOMContentLoaded', function () {

    /**
     * Mobile Menu Toggle Functionality
     */
    const mobileMenuButton = document.getElementById('mobile-menu-button');
    const mobileMenu = document.getElementById('mobile-menu');

    if (mobileMenuButton && mobileMenu) {
        mobileMenuButton.addEventListener('click', function () {
            mobileMenu.classList.toggle('active');
        });
        // Optional: Close menu when a link is clicked
        mobileMenu.querySelectorAll('a').forEach(link => {
            link.addEventListener('click', () => {
                mobileMenu.classList.remove('active');
            });
        });
    }


    /**
     * Hero Section Image Carousel
     */
    const heroCarousel = () => {
        const slides = document.querySelectorAll('.hero-slide');
        if (slides.length === 0) return; // Don't run if no slides exist

        const dots = document.querySelectorAll('.hero-dots button');
        let currentSlide = 0;
        let interval;

        function showSlide(index) {
            // Update slides
            slides.forEach((slide, i) => {
                slide.dataset.active = (i === index);
            });
            // Update dots
            dots.forEach((dot, i) => {
                dot.classList.toggle('active', i === index);
            });
            currentSlide = index;
        }

        function nextSlide() {
            showSlide((currentSlide + 1) % slides.length);
        }

        function startCarousel() {
            clearInterval(interval); // Clear any existing interval
            interval = setInterval(nextSlide, 5000);
        }

        // Event listeners for dots
        dots.forEach((dot, index) => {
            dot.addEventListener('click', () => {
                showSlide(index);
                startCarousel(); // Reset interval on manual click
            });
        });

        // Initialize
        showSlide(0);
        startCarousel();
    };
    heroCarousel();


    /**
     * Animated Member Counter
     */
    const animateCountUp = (element) => {
        const targetCount = 34; // The final number to count to
        const duration = 2000; // Duration in milliseconds
        const startTime = Date.now();
        const startCount = 0;

        function updateCount() {
            const elapsedTime = Date.now() - startTime;
            const progress = Math.min(elapsedTime / duration, 1);
            const currentCount = Math.floor(progress * targetCount);
            element.textContent = currentCount;

            if (progress < 1) {
                requestAnimationFrame(updateCount);
            } else {
                element.textContent = targetCount;
            }
        }
        requestAnimationFrame(updateCount);
    }

    const memberCountElement = document.getElementById('memberCount');
    if (memberCountElement) {
        // Use Intersection Observer to trigger the animation only when it's visible
        const observer = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    animateCountUp(memberCountElement);
                    observer.unobserve(entry.target); // Animate only once
                }
            });
        }, { threshold: 0.5 }); // Trigger when 50% of the element is visible

        observer.observe(memberCountElement);
    }


    /**
     * Star Background Animation
     */
    const starsContainer = document.getElementById('stars-container');
    if (starsContainer) {
        const fragment = document.createDocumentFragment();
        const starCount = 100;

        for (let i = 0; i < starCount; i++) {
            const star = document.createElement('div');
            star.classList.add('star');
            const size = Math.random() * 2 + 1;
            const delay = Math.random() * 5;
            const duration = 5 + Math.random() * 10;

            star.style.width = `${size}px`;
            star.style.height = `${size}px`;
            star.style.left = `${Math.random() * 100}%`;
            star.style.top = `${Math.random() * 100}%`;
            star.style.animationDelay = `${delay}s`;
            star.style.animationDuration = `${duration}s`;

            fragment.appendChild(star);
        }
        starsContainer.appendChild(fragment);
    }

    /**
     * Form Submission Handler (Placeholder)
     */
    const contactForm = document.getElementById('contact-form');
    if (contactForm) {
        contactForm.addEventListener('submit', function (e) {
            e.preventDefault();
            // Add your form submission logic here (e.g., using fetch to send data to your Flask backend)
            console.log('Form submitted!');
            const notification = document.getElementById('notification');
            notification.textContent = 'Thank you for your message!';
            notification.style.color = '#34d399';
            contactForm.reset();
        });
    }

});