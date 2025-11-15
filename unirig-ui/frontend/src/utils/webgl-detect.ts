/**
 * WebGL capability detection utility.
 * Checks for WebGL 2.0 support and provides fallback detection.
 */

export interface WebGLCapabilities {
  hasWebGL: boolean;
  hasWebGL2: boolean;
  renderer: string;
  version: string;
  maxTextureSize: number;
  maxVertexUniforms: number;
  errorMessage?: string;
}

/**
 * Detect WebGL and WebGL 2.0 support in the browser.
 * 
 * @returns WebGLCapabilities object with support details
 */
export function detectWebGLSupport(): WebGLCapabilities {
  // Create a temporary canvas for detection
  const canvas = document.createElement('canvas');
  
  let hasWebGL2 = false;
  let hasWebGL = false;
  let renderer = 'Unknown';
  let version = 'Unknown';
  let maxTextureSize = 0;
  let maxVertexUniforms = 0;
  let errorMessage: string | undefined;

  try {
    // Try WebGL 2.0 first
    const gl2 = canvas.getContext('webgl2');
    if (gl2) {
      hasWebGL2 = true;
      hasWebGL = true;
      
      const debugInfo = gl2.getExtension('WEBGL_debug_renderer_info');
      if (debugInfo) {
        renderer = gl2.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL) || 'WebGL 2.0';
        version = gl2.getParameter(gl2.VERSION) || 'WebGL 2.0';
      } else {
        renderer = 'WebGL 2.0 (debug info unavailable)';
        version = gl2.getParameter(gl2.VERSION) || 'WebGL 2.0';
      }
      
      maxTextureSize = gl2.getParameter(gl2.MAX_TEXTURE_SIZE) || 0;
      maxVertexUniforms = gl2.getParameter(gl2.MAX_VERTEX_UNIFORM_VECTORS) || 0;
    } else {
      // Fallback to WebGL 1.0
      const gl1 = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
      if (gl1 && (gl1 instanceof WebGLRenderingContext)) {
        hasWebGL = true;
        
        const debugInfo = gl1.getExtension('WEBGL_debug_renderer_info');
        if (debugInfo) {
          renderer = gl1.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL) || 'WebGL 1.0';
          version = gl1.getParameter(gl1.VERSION) || 'WebGL 1.0';
        } else {
          renderer = 'WebGL 1.0 (debug info unavailable)';
          version = gl1.getParameter(gl1.VERSION) || 'WebGL 1.0';
        }
        
        maxTextureSize = gl1.getParameter(gl1.MAX_TEXTURE_SIZE) || 0;
        maxVertexUniforms = gl1.getParameter(gl1.MAX_VERTEX_UNIFORM_VECTORS) || 0;
        
        errorMessage = 'WebGL 2.0 is not supported. Some features may not work correctly. Please update your browser or graphics drivers.';
      } else {
        errorMessage = 'WebGL is not supported in your browser. Please use a modern browser with WebGL support (Chrome 56+, Firefox 51+, Safari 15+).';
      }
    }
  } catch (error) {
    errorMessage = `Error detecting WebGL support: ${error instanceof Error ? error.message : 'Unknown error'}`;
  }

  return {
    hasWebGL,
    hasWebGL2,
    renderer,
    version,
    maxTextureSize,
    maxVertexUniforms,
    errorMessage,
  };
}

/**
 * Check if the browser meets minimum requirements for 3D model viewing.
 * 
 * @returns True if requirements are met, false otherwise
 */
export function meetsMinimumRequirements(): boolean {
  const capabilities = detectWebGLSupport();
  
  // Require WebGL (WebGL 2.0 preferred but 1.0 acceptable)
  if (!capabilities.hasWebGL) {
    return false;
  }
  
  // Check minimum texture size (require at least 2048x2048)
  if (capabilities.maxTextureSize < 2048) {
    return false;
  }
  
  return true;
}

/**
 * Get a user-friendly error message for WebGL issues.
 * 
 * @param capabilities WebGL capabilities object
 * @returns Error message string or undefined if no error
 */
export function getWebGLErrorMessage(capabilities: WebGLCapabilities): string | undefined {
  if (!capabilities.hasWebGL) {
    return 'Your browser does not support WebGL, which is required for 3D model viewing. Please use a modern browser like Chrome, Firefox, or Safari.';
  }
  
  if (!capabilities.hasWebGL2) {
    return 'Your browser supports WebGL 1.0 but not WebGL 2.0. Some advanced features may not work. Consider updating your browser for the best experience.';
  }
  
  if (capabilities.maxTextureSize < 2048) {
    return 'Your graphics capabilities are below the minimum requirements. Models may not display correctly.';
  }
  
  return capabilities.errorMessage;
}
