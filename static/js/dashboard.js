document.addEventListener('DOMContentLoaded', function() {
    // Initialize DataTables
    if (document.getElementById('casesTable')) {
        $('#casesTable').DataTable({
            responsive: true,
            order: [[1, 'desc']], // Sort by timestamp column (descending)
            language: {
                search: "_INPUT_",
                searchPlaceholder: "Search cases...",
                lengthMenu: "Show _MENU_ cases per page",
                info: "Showing _START_ to _END_ of _TOTAL_ cases",
                infoEmpty: "Showing 0 to 0 of 0 cases",
                infoFiltered: "(filtered from _MAX_ total cases)"
            },
            columnDefs: [
                { orderable: false, targets: [3, 7] } // Disable sorting for photos and actions columns
            ],
            pageLength: 10,
            lengthMenu: [
                [10, 25, 50, -1],
                [10, 25, 50, "All"]
            ]
        });
    }
    
    // Add event listeners to all status change links
    document.querySelectorAll('.status-change').forEach(link => {
        link.addEventListener('click', handleStatusChange);
    });
    
    // Function to handle status change
    function handleStatusChange(event) {
        event.preventDefault();
        
        const caseId = this.getAttribute('data-case-id');
        const newStatus = this.getAttribute('data-status');
        
        // Show confirmation dialog
        if (!confirm(`Are you sure you want to change the status to "${newStatus}"?`)) {
            return;
        }
        
        // Add loading state
        const originalText = this.innerHTML;
        this.innerHTML = `<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Updating...`;
        this.classList.add('disabled');
        
        // Send AJAX request to update status
        fetch(`/api/update-status/${caseId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                status: newStatus
            }),
        })
        .then(response => response.json())
        .then(data => {
            // Reset button state
            this.innerHTML = originalText;
            this.classList.remove('disabled');
            
            if (data.success) {
                // Show success message
                const toastHTML = `
                <div class="position-fixed bottom-0 end-0 p-3" style="z-index: 5">
                    <div class="toast align-items-center text-white bg-success border-0" role="alert" aria-live="assertive" aria-atomic="true">
                        <div class="d-flex">
                            <div class="toast-body">
                                <i class="bi bi-check-circle me-2"></i>Status updated successfully!
                            </div>
                            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
                        </div>
                    </div>
                </div>`;
                
                document.body.insertAdjacentHTML('beforeend', toastHTML);
                const toastEl = document.body.lastElementChild.querySelector('.toast');
                const toast = new bootstrap.Toast(toastEl, { delay: 3000 });
                toast.show();
                
                // Reload the page after a short delay
                setTimeout(() => {
                    window.location.reload();
                }, 1000);
            } else {
                alert('Error updating status: ' + (data.message || 'Unknown error'));
            }
        })
        .catch(error => {
            // Reset button state
            this.innerHTML = originalText;
            this.classList.remove('disabled');
            
            console.error('Error:', error);
            alert('An error occurred while updating the status. Please try again.');
        });
    }
}); 