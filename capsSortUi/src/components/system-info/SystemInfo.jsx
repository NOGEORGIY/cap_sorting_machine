function SystemInfo() {
  return (
    <section className="system-info">
      <div className="system-info__block system-info__block--stats">
        <h2 className="system-info__title">Показатели</h2>

        <ul className="system-info__list">
          <li className="system-info__item">
            <span className="system-info__label">Обработано крышек:</span>
            <span className="system-info__value">0</span>
          </li>

          <li className="system-info__item">
            <span className="system-info__label">Целевого цвета:</span>
            <span className="system-info__value">0</span>
          </li>

          <li className="system-info__item">
            <span className="system-info__label">Отбраковано:</span>
            <span className="system-info__value">0</span>
          </li>

          <li className="system-info__item">
            <span className="system-info__label">Текущая крышка:</span>
            <span className="system-info__value">—</span>
          </li>

          <li className="system-info__item">
            <span className="system-info__label">Ориентация:</span>
            <span className="system-info__value">—</span>
          </li>

          <li className="system-info__item">
            <span className="system-info__label">Распознанный цвет:</span>
            <span className="system-info__value">—</span>
          </li>
        </ul>
      </div>

      <div className="system-info__block system-info__block--alerts">
        <h2 className="system-info__title">Аварии и предупреждения</h2>

        <div className="system-info__alerts">
          <p className="system-info__empty">Нет активных аварий</p>
        </div>
      </div>
    </section>
  );
}

export default SystemInfo;