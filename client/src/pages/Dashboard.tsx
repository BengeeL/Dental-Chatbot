import { Container } from "react-bootstrap";
import "../styles/dashboard.css";
import { useEffect, useState } from "react";
import AppointmentTile from "../components/AppointmentTile";

export interface User {
  name: string;
  email: string;
  role: string;
  id: string;
}

export interface Appointment {
  id: string;
  date: string;
  time: string;
  status: string;
  dentist: string;
  patient: string;
}

export default function Dashboard() {
  const [currentAuthUser, setCurrentAuthUser] = useState<User | null>(null);
  const [ScheduledAppointments, setScheduledAppointments] = useState<
    Appointment[]
  >([]);
  const [PreviousVisit, setPreviousVisit] = useState<Appointment[]>([]);
  const [ScheduleModifyAppointment, setScheduleModifyAppointment] =
    useState<Appointment | null>(null);

  // Simulate fetching user data from an API
  useEffect(() => {
    const fetchUserData = async () => {
      // TODO: Fetch user data from API
      setCurrentAuthUser({
        name: "John Doe",
        email: "john@gmail.com",
        role: "patient",
        id: "123456",
      });
    };
    fetchUserData();
  }, []);

  // Simulate fetching appointments from an API
  useEffect(() => {
    const fetchAppointments = async () => {
      // TODO: Fetch appointments from API
      setScheduledAppointments([
        {
          id: "1",
          date: "2023-10-01",
          time: "10:00 AM",
          status: "Scheduled",
          dentist: "Dr. Smith",
          patient: "John Doe",
        },
        {
          id: "2",
          date: "2023-10-05",
          time: "11:00 AM",
          status: "Scheduled",
          dentist: "Dr. Brown",
          patient: "John Doe",
        },
      ]);
      setPreviousVisit([
        {
          id: "3",
          date: "2023-09-15",
          time: "09:00 AM",
          status: "Completed",
          dentist: "Dr. Green",
          patient: "John Doe",
        },
      ]);
      setScheduleModifyAppointment({
        id: "4",
        date: "2023-10-10",
        time: "02:00 PM",
        status: "Scheduled",
        dentist: "Dr. White",
        patient: "John Doe",
      });
    };
    fetchAppointments();
  }, []);

  return (
    <>
      <Container className='mb-5'>
        {/* ************ HEADER ************ */}
        <div className='dashboard-tile dashboard-header'>
          <h2 className='dashboad-title'>
            ⚕️ Patient Portal
            {currentAuthUser?.name ? " - Welcome " + currentAuthUser?.name : ""}
          </h2>
        </div>

        {/* ************ DASHBOARD TILES ************ */}
        <div className='dashboard-container'>
          <div className='dashboard-left'>
            <div className='dashboard-tile'>
              <h2 className='dashboad-title'>Scheduled Appointments</h2>

              <div className='dashboard-list'>
                {ScheduledAppointments.length > 0 ? (
                  ScheduledAppointments.map((appointment) => (
                    <div key={appointment.id} className='dashboard-list-item'>
                      <AppointmentTile
                        appointment={appointment}
                        onClick={() => {
                          // Logic to handle appointment click
                          setScheduleModifyAppointment(appointment);
                        }}
                      />
                    </div>
                  ))
                ) : (
                  <p>No scheduled appointments</p>
                )}
              </div>
            </div>

            <div className='dashboard-tile'>
              <h2 className='dashboad-title'>Previous Visit</h2>

              <div className='dashboard-list'>
                {PreviousVisit.length > 0 ? (
                  PreviousVisit.map((appointment) => (
                    <div key={appointment.id} className='dashboard-list-item'>
                      <AppointmentTile
                        appointment={appointment}
                        onClick={() => {
                          // Logic to handle appointment click
                          setScheduleModifyAppointment(appointment);
                        }}
                      />
                    </div>
                  ))
                ) : (
                  <p>No previous visits</p>
                )}
              </div>
            </div>
          </div>

          <div className='dashboard-right'>
            <div className='dashboard-tile'>
              <h2 className='dashboad-title'>Schedule/Modify Appointment</h2>

              <div className='dashboard-list'>
                {ScheduleModifyAppointment ? (
                  <div className='dashboard-list-item'>
                    <p>{ScheduleModifyAppointment.date}</p>
                    <p>{ScheduleModifyAppointment.time}</p>
                    <p>{ScheduleModifyAppointment.status}</p>
                    <p>{ScheduleModifyAppointment.dentist}</p>
                    <p>{ScheduleModifyAppointment.patient}</p>
                  </div>
                ) : (
                  <p>No appointment selected</p>
                )}
                <button
                  className='btn btn-primary'
                  onClick={() => {
                    // Logic to schedule or modify an appointment
                    // This could be a modal or a redirect to another page
                    console.log("Schedule/Modify Appointment clicked");
                  }}
                >
                  Schedule/Modify Appointment
                </button>
                <div className='dashboard-list-item'>
                  <p>Appointment Details</p>
                  <p>Appointment ID: {ScheduleModifyAppointment?.id}</p>
                  <p>Patient ID: {currentAuthUser?.id}</p>
                  <p>Patient Name: {currentAuthUser?.name}</p>
                  <p>Patient Email: {currentAuthUser?.email}</p>
                  <p>Patient Role: {currentAuthUser?.role}</p>
                  <p>Appointment Status: {ScheduleModifyAppointment?.status}</p>
                  <p>
                    Appointment Dentist: {ScheduleModifyAppointment?.dentist}
                  </p>
                  <p>
                    Appointment Patient: {ScheduleModifyAppointment?.patient}
                  </p>
                  <p>Appointment Date: {ScheduleModifyAppointment?.date}</p>
                  <p>Appointment Time: {ScheduleModifyAppointment?.time}</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </Container>
    </>
  );
}
