// capsSortUi/src/components/SensorToggle.jsx
import { useState, useEffect } from 'react';
import { getMachineStatus, toggleSensor } from '../api/machineAPI';

function SensorToggle() {
  const [isActive, setIsActive] = useState(false);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const response = await getMachineStatus();
        const data = await response.json();
        setIsActive(data.proximity_active || false);
      } catch (error) {
        console.error('Ошибка получения статуса датчика:', error);
      }
    };
    fetchStatus();
  }, []);

  const handleToggle = async () => {
    setLoading(true);
    try {
      const newState = !isActive;
      await toggleSensor(newState);
      setIsActive(newState);
    } catch (error) {
      console.error('Ошибка переключения датчика:', error);
      alert('Не удалось переключить режим датчика');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="sensor-toggle">
      <span className={`sensor-toggle__mode ${isActive ? 'sensor-toggle__mode--emergency' : 'sensor-toggle__mode--basic'}`}>
        {isActive ? 'EMERGENCY' : 'BASIC'}
      </span>
      
      <button
        className={`sensor-toggle__button ${isActive ? 'sensor-toggle__button--active' : ''}`}
        onClick={handleToggle}
        disabled={loading}
      >
        <div className="sensor-toggle__slider">
          <div className={`sensor-toggle__circle ${isActive ? 'sensor-toggle__circle--active' : ''}`} />
        </div>
      </button>
      
      <span className="sensor-toggle__status">
        {isActive ? 'ВКЛ' : 'ВЫКЛ'}
      </span>
    </div>
  );
}

export default SensorToggle;