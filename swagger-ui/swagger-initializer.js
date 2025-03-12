window.onload = function() {
  window.ui = SwaggerUIBundle({
      url: "/openapi.json",  // Asegúrate de que apunte a la API local
      dom_id: "#swagger-ui",
      deepLinking: true,
      presets: [
          SwaggerUIBundle.presets.apis,
          SwaggerUIStandalonePreset
      ],
      layout: "StandaloneLayout"
  });
};