export function buildReportPreviewFrameSrcDoc(htmlDocument) {
  if (!htmlDocument || typeof htmlDocument !== "string" || !htmlDocument.trim()) {
    return "";
  }

  return `<!doctype html>
<html>
  <head>
    <meta charset="utf-8" />
    <style>
      html, body {
        margin: 0;
        background: #f8fafc;
        overflow: hidden;
        pointer-events: none;
      }
      #preview-scale {
        width: 794px;
        min-height: 1123px;
        transform: scale(0.22);
        transform-origin: top left;
      }
    </style>
  </head>
  <body>
    <div id="preview-scale">${htmlDocument}</div>
  </body>
</html>`;
}
