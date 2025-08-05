// Count up animation
function animateCountUp(targetCount, element) {
    const duration = 800; // 2 seconds for a smoother count
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

    updateCount();
}

// This event listener ensures the DOM is fully loaded before the script runs.
document.addEventListener('DOMContentLoaded', function() {
    // Mobile menu toggle
    const mobileMenuButton = document.getElementById('mobile-menu-button');
    const mobileMenu = document.getElementById('mobile-menu');

    if (mobileMenuButton && mobileMenu) {
        mobileMenuButton.addEventListener('click', function() {
            mobileMenu.classList.toggle('hidden');
        });
    }

    const memberCounter = document.getElementById('memberCount');
    const memberCounterDesktop = document.getElementById('memberCountDesktop');

    // Animate the counters if they exist
    if (memberCounter && memberCounterDesktop) {
        memberCounter.textContent = '0';
        memberCounterDesktop.textContent = '0';
        // Use a small timeout to ensure visibility before animation starts
        setTimeout(() => {
            animateCountUp(34, memberCounter);
            animateCountUp(34, memberCounterDesktop);
        }, 500);
    }

    // Optimized star animation
    const starsContainer = document.getElementById('stars-container');
    if (starsContainer) {
        const fragment = document.createDocumentFragment();
        const starCount = 100;

        for (let i = 0; i < starCount; i++) {
            const star = document.createElement('div');
            star.classList.add('star');

            const size = Math.random() * 2 + 1;
            star.style.cssText = `
                width: ${size}px;
                height: ${size}px;
                left: ${Math.random() * 100}%;
                top: ${Math.random() * 100}%;
                opacity: ${Math.random()};
                animation: twinkle ${5 + Math.random() * 10}s infinite ${Math.random() * 5}s ease-in-out;
            `;

            fragment.appendChild(star);
        }

        starsContainer.appendChild(fragment);

        // Add animation keyframes dynamically
        const style = document.createElement('style');
        style.textContent = `
            @keyframes twinkle {
                0%, 100% { opacity: 0; }
                50% { opacity: 1; }
            }
        `;
        document.head.appendChild(style);
    }

    // Smooth scrolling for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();

            const targetId = this.getAttribute('href');
            if (targetId === '#') return;

            const targetElement = document.querySelector(targetId);
            if (targetElement) {
                // The offset adjusts for the fixed navigation bar height
                window.scrollTo({
                    top: targetElement.offsetTop - 80,
                    behavior: 'smooth'
                });
            }
        });
    });
});
document.addEventListener('DOMContentLoaded', function() {
    // ... (keep all your existing JavaScript code for the menu, counter, stars, etc.)

    const contactForm = document.getElementById('contact-form');
    const notification = document.getElementById('notification');

    if (contactForm) {
        contactForm.addEventListener('submit', function(e) {
            e.preventDefault(); // Prevent the default page reload

            const formData = new FormData(this);
            const submitButton = this.querySelector('button[type="submit"]');

            // Disable button and show a "sending" message
            submitButton.disabled = true;
            submitButton.textContent = 'Sending...';
            notification.textContent = '';

            fetch('/', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    notification.textContent = 'Message sent successfully!';
                    notification.style.color = '#34d399'; // Green color for success
                    contactForm.reset(); // Clear the form fields
                } else {
                    notification.textContent = 'An error occurred. Please try again.';
                    notification.style.color = '#f87171'; // Red color for error
                }
            })
            .catch(error => {
                console.error('Error:', error);
                notification.textContent = 'A network error occurred. Please try again.';
                notification.style.color = '#f87171';
            })
            .finally(() => {
                // Re-enable the button after the request is complete
                submitButton.disabled = false;
                submitButton.textContent = 'Sign Up Now';
            });
        });
    }
});