import { Appointment } from "../pages/Dashboard";

export default function AppointmentTile({
  appointment,
  onClick,
}: {
  appointment: Appointment;
  onClick: () => void;
}) {
  const handleClick = () => {
    onClick();
  };

  return (
    <div className='appointment-tile' onClick={handleClick}>
      <h3>{appointment.dentist}</h3>
      <p>Date: {appointment.date}</p>
      <p>Time: {appointment.time}</p>
      <p>Status: {appointment.status}</p>
    </div>
  );
}
