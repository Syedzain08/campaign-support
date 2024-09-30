document.addEventListener("DOMContentLoaded", function() {
    const alertBanners = document.querySelectorAll(".alert");
    
    alertBanners.forEach(alertBanner => {
        const bannerCloseBtn = alertBanner.querySelector(".banner-close-btn");
        
        if (bannerCloseBtn) {
            bannerCloseBtn.addEventListener("click", () => {
                alertBanner.style.display = "none";
            });
        }
    });
});