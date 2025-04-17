document.addEventListener('DOMContentLoaded', function() {
    // Get DOM elements
    const getLocationBtn = document.getElementById('get-location');
    const latitudeInput = document.getElementById('latitude');
    const longitudeInput = document.getElementById('longitude');
    const locationStatus = document.getElementById('location-status');
    const imageInput = document.getElementById('images');
    const imagePreviewContainer = document.getElementById('image-preview');
    
    // Add event listeners
    getLocationBtn.addEventListener('click', getLocation);
    imageInput.addEventListener('change', handleImagePreview);
    
    // Automatically try to get location on page load
    tryGeolocation();
    
    // Function to get the user's location
    function getLocation() {
        locationStatus.textContent = 'Requesting location...';
        locationStatus.style.color = '#6c757d';
        
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                showPosition,
                showError,
                {
                    enableHighAccuracy: true,
                    timeout: 10000,
                    maximumAge: 0
                }
            );
        } else {
            locationStatus.textContent = 'Geolocation is not supported by this browser.';
            locationStatus.style.color = '#dc3545';
        }
    }
    
    // Function to try getting location automatically on page load
    function tryGeolocation() {
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                showPosition,
                function(error) {
                    // Silent failure - user will use the button if they want to enable
                    console.log('Auto geolocation failed:', error.message);
                },
                {
                    enableHighAccuracy: true,
                    timeout: 10000,
                    maximumAge: 0
                }
            );
        }
    }
    
    // Function to display the position
    function showPosition(position) {
        latitudeInput.value = position.coords.latitude;
        longitudeInput.value = position.coords.longitude;
        locationStatus.textContent = 'Location obtained successfully!';
        locationStatus.style.color = '#198754';
    }
    
    // Function to handle errors
    function showError(error) {
        switch(error.code) {
            case error.PERMISSION_DENIED:
                locationStatus.textContent = 'User denied the request for Geolocation.';
                break;
            case error.POSITION_UNAVAILABLE:
                locationStatus.textContent = 'Location information is unavailable.';
                break;
            case error.TIMEOUT:
                locationStatus.textContent = 'The request to get user location timed out.';
                break;
            case error.UNKNOWN_ERROR:
                locationStatus.textContent = 'An unknown error occurred.';
                break;
        }
        locationStatus.style.color = '#dc3545';
    }
    
    // Function to handle image preview
    function handleImagePreview() {
        imagePreviewContainer.innerHTML = '';
        
        if (imageInput.files.length > 0) {
            for (let i = 0; i < imageInput.files.length; i++) {
                const file = imageInput.files[i];
                
                // Only process image files
                if (!file.type.match('image.*')) {
                    continue;
                }
                
                const reader = new FileReader();
                
                reader.onload = (function(theFile) {
                    return function(e) {
                        // Create preview container
                        const colDiv = document.createElement('div');
                        colDiv.className = 'col-md-3 col-sm-4 col-6';
                        
                        const previewContainer = document.createElement('div');
                        previewContainer.className = 'img-preview-container';
                        
                        // Create image element
                        const img = document.createElement('img');
                        img.className = 'img-preview';
                        img.src = e.target.result;
                        img.title = escape(theFile.name);
                        
                        // Add remove button
                        const removeBtn = document.createElement('span');
                        removeBtn.className = 'img-preview-remove';
                        removeBtn.innerHTML = '×';
                        removeBtn.addEventListener('click', function() {
                            colDiv.remove();
                            // Note: Can't actually remove from FileList, but this gives visual feedback
                        });
                        
                        // Append elements
                        previewContainer.appendChild(img);
                        previewContainer.appendChild(removeBtn);
                        colDiv.appendChild(previewContainer);
                        imagePreviewContainer.appendChild(colDiv);
                    };
                })(file);
                
                // Read in the image file as a data URL
                reader.readAsDataURL(file);
            }
        }
    }
}); 