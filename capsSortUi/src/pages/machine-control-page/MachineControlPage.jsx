import { useState } from "react";
import PageHeader from "../../components/page-header/PageHeader";
import MachineControls from "../../components/machine-controls/MachineControls";
import MachineStatus from "../../components/machine-status/MachineStatus";
import ColorSelect from "../../components/color-select/ColorSelect";
import MachineBlocks from "../../components/machine-blocks/MachineBlocks";
import MessageLog from "../../components/message-log/MessageLog";
import { COLORS } from "../../data/colors";
import { MACHINE_BLOCKS } from "../../data/machineBlocks";
import { INITIAL_MESSAGES } from "../../data/messages";
import {
  startMachine,
  stopMachine,
  setMachineColor,
} from "../../api/machineAPI";
import MachineScheme from "../../components/machine-scheme/MachineScheme";
import SystemInfo from "../../components/system-info/SystemInfo";
import PageFooter from "../../components/page-footer/PageFooter";

function MachineControlPage() {
  const [machineStatus, setMachineStatus] = useState("ОСТАНОВЛЕНА");
  const [selectedColor, setSelectedColor] = useState("blue");
  const [messages, setMessages] = useState(INITIAL_MESSAGES);

  const addMessage = (text) => {
    setMessages((prev) => [{ id: Date.now(), text }, ...prev]);
  };

  const handleStartClick = async () => {
    try {
      const data = await startMachine();
      setMachineStatus("ЗАПУЩЕНА");
      addMessage(data?.message || "Команда: система запущена");
    } catch (error) {
      console.error(error);
      addMessage("Ошибка запуска системы");
    }
  };

  const handleStopClick = async () => {
    try {
      const data = await stopMachine();
      setMachineStatus("ОСТАНОВЛЕНА");
      addMessage(data?.message || "Команда: система остановлена");
    } catch (error) {
      console.error(error);
      addMessage("Ошибка остановки системы");
    }
  };

  const handleColorChange = async (event) => {
    const nextColor = event.target.value;

    try {
      const data = await setMachineColor(nextColor);
      setSelectedColor(nextColor);

      const selectedOption = COLORS.find((color) => color.value === nextColor);

      addMessage(
        data?.message ||
          `Выбран целевой цвет: ${selectedOption?.label ?? nextColor}`,
      );
    } catch (error) {
      console.error(error);
      addMessage("Ошибка выбора цвета");
    }
  };

  return (
    <div className="wrapper">
      <main className="content">
        <div className="container">
          <div className="machine-control-page">
            <PageHeader title="Система управления сортировкой пластиковых крышек" />

            <section className="machine-control-page__toolbar">
              <MachineControls
                onStart={handleStartClick}
                onStop={handleStopClick}
              />

              <div className="machine-control-page__settings">
                <MachineStatus status={machineStatus} />

                <ColorSelect
                  label="Целевой цвет:"
                  value={selectedColor}
                  options={COLORS}
                  onChange={handleColorChange}
                />
              </div>
            </section>
            <section className="machine-control-page__scheme">
              <MachineScheme />
            </section>
            <section className="machine-control-page__content">
              
              <MachineBlocks blocks={MACHINE_BLOCKS} />
              <MessageLog messages={messages} />
            </section>
            <SystemInfo />
            <PageFooter />
          </div>
        </div>
      </main>
    </div>
  );
}

export default MachineControlPage;
