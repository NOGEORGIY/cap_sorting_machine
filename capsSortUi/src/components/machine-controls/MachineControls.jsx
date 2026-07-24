function MachineControls({ onStart, onStop }) {
  return (
    <section className="machine-controls">
      <div className="machine-controls__actions">
        <button
          className="machine-controls__button machine-controls__button--type-start"
          type="button"
          onClick={onStart}
        >
          Запустить
        </button>

        <button
          className="machine-controls__button machine-controls__button--type-stop"
          type="button"
          onClick={onStop}
        >
          Остановить
        </button>
      </div>
    </section>
  );
}

export default MachineControls;
