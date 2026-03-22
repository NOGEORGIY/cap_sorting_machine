function MachineStatus({ status }) {
  return (
    <div className="machine-status">
      <span className="machine-status__label">Статус машины:</span>
      <span className="machine-status__value">{status}</span>
    </div>
  );
}

export default MachineStatus;
