import { useEffect, useRef } from "react";

function MachineScheme() {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");

    // очистка
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // стили по умолчанию
    ctx.strokeStyle = "#444";
    ctx.fillStyle = "#ffffff";
    ctx.lineWidth = 2;
    ctx.font = "16px Arial";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";

    const drawBlock = (x, y, w, h, text) => {
      ctx.beginPath();
      ctx.rect(x, y, w, h);
      ctx.fill();
      ctx.stroke();
      ctx.fillStyle = "#222";
      ctx.fillText(text, x + w / 2, y + h / 2);
      ctx.fillStyle = "#ffffff";
    };

    const drawArrow = (x1, y1, x2, y2) => {
      const headlen = 10;
      const angle = Math.atan2(y2 - y1, x2 - x1);

      ctx.beginPath();
      ctx.moveTo(x1, y1);
      ctx.lineTo(x2, y2);
      ctx.stroke();

      ctx.beginPath();
      ctx.moveTo(x2, y2);
      ctx.lineTo(
        x2 - headlen * Math.cos(angle - Math.PI / 6),
        y2 - headlen * Math.sin(angle - Math.PI / 6)
      );
      ctx.lineTo(
        x2 - headlen * Math.cos(angle + Math.PI / 6),
        y2 - headlen * Math.sin(angle + Math.PI / 6)
      );
      ctx.closePath();
      ctx.fillStyle = "#444";
      ctx.fill();
      ctx.fillStyle = "#ffffff";
    };

    // верхняя линия
    drawBlock(40, 120, 100, 60, "Входной бак");
    drawBlock(180, 120, 100, 60, "Подача");
    drawBlock(320, 120, 100, 60, "Камера 1");
    drawBlock(460, 120, 100, 60, "Переворот");
    drawBlock(600, 120, 100, 60, "Конвейер");
    drawBlock(740, 120, 100, 60, "Камера 2");

    drawArrow(140, 150, 180, 150);
    drawArrow(280, 150, 320, 150);
    drawArrow(420, 150, 460, 150);
    drawArrow(560, 150, 600, 150);
    drawArrow(700, 150, 740, 150);

    // нижние баки
    drawBlock(430, 280, 140, 60, "Бак цели");
    drawBlock(670, 280, 140, 60, "Бак отброса");

    drawArrow(650, 180, 500, 280);
    drawArrow(790, 180, 740, 280);
  }, []);

  return (
    <div className="machine-scheme">
      <canvas
        ref={canvasRef}
        width={900}
        height={400}
      />
    </div>
  );
}

export default MachineScheme;