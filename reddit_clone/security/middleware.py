class SecurityHeadersMiddleware:
    """
    Middleware to add security headers to all responses.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        
        # Content-Security-Policy
        # Prevents XSS attacks by controlling which resources can be loaded
        response['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "img-src 'self' data: blob: https://*; "
            "font-src 'self' https://cdn.jsdelivr.net; "
            "connect-src 'self' wss://*; "
            "media-src 'self' blob:; "
            "object-src 'none'; "
            "frame-src 'none'; "
            "base-uri 'self'; "
            "form-action 'self'; "
        )
        
        # X-Content-Type-Options
        # Prevents MIME type sniffing
        response['X-Content-Type-Options'] = 'nosniff'
        
        # X-Frame-Options
        # Prevents clickjacking
        response['X-Frame-Options'] = 'DENY'
        
        # Referrer-Policy
        # Controls what information is sent in the Referer header
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Permissions-Policy
        # Restricts browser features
        response['Permissions-Policy'] = (
            "camera=(), "
            "microphone=(), "
            "geolocation=(), "
            "payment=(), "
            "usb=(), "
            "accelerometer=(), "
            "gyroscope=()"
        )
        
        # Strict-Transport-Security (HSTS)
        # Enforces HTTPS
        response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains; preload'
        
        # X-XSS-Protection
        # Enables XSS filtering in some browsers
        response['X-XSS-Protection'] = '1; mode=block'
        
        return response 