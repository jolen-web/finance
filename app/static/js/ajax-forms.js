/**
 * AJAX Form Handler - Submits forms via AJAX for better UX
 */

class AJAXFormHandler {
  constructor() {
    this.init();
  }

  init() {
    // Find all forms with data-ajax attribute
    document.querySelectorAll('form[data-ajax]').forEach((form) => {
      form.addEventListener('submit', (e) => this.handleSubmit(e, form));
    });
  }

  async handleSubmit(event, form) {
    event.preventDefault();

    const formData = new FormData(form);
    const url = form.action;
    const method = form.method.toUpperCase();
    const submitBtn = form.querySelector('button[type="submit"]');

    // Show loading state
    if (submitBtn) {
      submitBtn.disabled = true;
      submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Submitting...';
    }

    try {
      const response = await fetch(url, {
        method: method,
        body: formData,
        headers: {
          'X-Requested-With': 'XMLHttpRequest',
        },
      });

      const data = await response.json();

      if (response.ok) {
        // Success
        if (data.message) {
          window.toast.success(data.message);
        }

        // Redirect if specified
        if (data.redirect) {
          setTimeout(() => {
            window.location.href = data.redirect;
          }, 1500);
        } else if (data.reload) {
          // Reload page if specified
          setTimeout(() => {
            window.location.reload();
          }, 1000);
        }

        // Clear form if specified
        if (data.clear_form) {
          form.reset();
        }
      } else {
        // Error
        if (data.message) {
          window.toast.error(data.message);
        }

        // Show field errors if provided
        if (data.errors) {
          Object.entries(data.errors).forEach(([field, error]) => {
            const input = form.querySelector(`[name="${field}"]`);
            if (input) {
              input.classList.add('is-invalid');
              const feedback = input.parentElement.querySelector('.invalid-feedback');
              if (feedback) {
                feedback.textContent = error;
              }
            }
          });
        }
      }
    } catch (error) {
      console.error('AJAX submission error:', error);
      window.toast.error('An error occurred. Please try again.');
    } finally {
      // Restore button state
      if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.innerHTML = submitBtn.dataset.originalText || 'Submit';
      }
    }
  }
}

// Initialize AJAX form handler when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  // Store original button text before modifying
  document.querySelectorAll('button[type="submit"]').forEach((btn) => {
    btn.dataset.originalText = btn.innerHTML;
  });

  window.ajaxFormHandler = new AJAXFormHandler();
});

// Add validation feedback styling
const ajaxFormStyle = document.createElement('style');
ajaxFormStyle.textContent = `
  .is-invalid {
    border-color: var(--danger) !important;
  }

  .invalid-feedback {
    display: block;
    color: var(--danger);
    font-size: 0.875rem;
    margin-top: 0.25rem;
  }

  .form-control.is-invalid:focus,
  .form-select.is-invalid:focus {
    border-color: var(--danger);
    box-shadow: 0 0 0 3px rgba(239, 68, 68, 0.1);
  }
`;
document.head.appendChild(ajaxFormStyle);
