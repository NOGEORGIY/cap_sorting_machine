// capsSortUi/src/components/lid-stack/LidStack.jsx
import { useState, useEffect, useRef } from 'react';

function LidStack() {
  const [stack, setStack] = useState([]);
  const [isConnected, setIsConnected] = useState(false);
  const wsRef = useRef(null);

  useEffect(() => {
    const ws = new WebSocket('ws://localhost:8000/ws/stack');
    wsRef.current = ws;

    ws.onopen = () => {
      setIsConnected(true);
      console.log('✅ WebSocket стека подключен');
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'stack_update') {
        setStack(data.stack);
      }
    };

    ws.onclose = () => {
      setIsConnected(false);
      console.log('❌ WebSocket стека отключен');
    };

    return () => {
      ws.close();
    };
  }, []);

  return (
    <div className="lid-stack">
      <div className="lid-stack__header">
        <h3 className="lid-stack__title">📦 Стек крышек</h3>
        <span className={`lid-stack__status ${isConnected ? 'connected' : 'disconnected'}`}>
          {isConnected ? '🟢 онлайн' : '🔴 офлайн'}
        </span>
        <span className="lid-stack__count">Всего: {stack.length}</span>
      </div>
      
      <div className="lid-stack__list">
        {stack.length === 0 ? (
          <p className="lid-stack__empty">Стек пуст</p>
        ) : (
          <div className="lid-stack__items">
            {stack.map((item, index) => (
              <div 
                key={index} 
                className={`lid-stack__item ${item.is_success ? 'success' : 'fail'}`}
                style={{ 
                  borderLeftColor: item.detected_color,
                  borderLeftWidth: '4px',
                  borderLeftStyle: 'solid'
                }}
              >
                <span className="lid-stack__color">
                  {item.detected_color.toUpperCase()}
                </span>
                <span className="lid-stack__target">
                  → {item.target_color.toUpperCase()}
                </span>
                <span className="lid-stack__result">
                  {item.is_success ? '✅' : '❌'}
                </span>
                <span className="lid-stack__time">
                  {new Date(item.timestamp * 1000).toLocaleTimeString()}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default LidStack;