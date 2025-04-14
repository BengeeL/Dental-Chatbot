import { useState } from "react";
import {
  Alert,
  Button,
  Col,
  Container,
  Form,
  Nav,
  Row,
  Spinner,
} from "react-bootstrap";
import "@/styles/authenticationForm.css";
import "bootstrap/dist/css/bootstrap.min.css";

export default function AuthenticationForm() {
  // STATES
  const [email, setemail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");

  const [activeTab, setActiveTab] = useState("login");
  const [authError, setAuthError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  // FORM HANDLERS
  const handleSubmit = async (e: { preventDefault: () => void }) => {
    e.preventDefault();
    setIsSubmitting(true);
    setAuthError("");

    if (!email || !password) {
      setAuthError("Email and password are required.");
      setIsSubmitting(false);
      return;
    }

    if (activeTab === "login") {
      // TODO: Login logic
    } else {
      // TODO: Register logic
    }

    setIsSubmitting(false);
  };

  // Layout Base Model from https://mdbootstrap.com/docs/standard/extended/login/
  return (
    <>
      <section className='section-auth'>
        <div className='container py-5 h-100'>
          <div className='row d-flex justify-content-center align-items-center h-100'>
            <div className='col col-xl-10'>
              <div className='card card-auth'>
                <div className='row g-0'>
                  {/* IMAGE */}
                  <div className='col-md-6 col-lg-5 d-none d-md-block'>
                    <img
                      src='/auth-image.webp'
                      alt='authentication form'
                      className='img-fluid image-auth'
                    />
                  </div>

                  {/* FORM */}
                  <div className='col-md-6 col-lg-6 d-flex align-items-top'>
                    <div className='card-body p-2 p-lg-5 text-black'></div>
                    <Container className='p-2'>
                      <h1 className='clinic-name'>
                        PASTE
                        <br />
                        DENTAL
                      </h1>
                      <Row className='justify-content-md-center'>
                        <Col>
                          {/* LOGIN / REGISTER - TAB */}
                          <Nav
                            variant='tabs'
                            activeKey={activeTab}
                            onSelect={(k) => {
                              if (k) setActiveTab(k);
                            }}
                            className='nav-tabs'
                          >
                            <Nav.Item>
                              <Nav.Link eventKey='login'>Login</Nav.Link>
                            </Nav.Item>
                            <Nav.Item>
                              <Nav.Link eventKey='signup'>Sign Up</Nav.Link>
                            </Nav.Item>
                          </Nav>

                          {/* REGISTER FIELDS */}
                          {activeTab === "signup" && (
                            <>
                              <Form.Group className='mb-3  mt-3'>
                                <Form.Label>Name</Form.Label>
                                <Form.Control
                                  type='text'
                                  placeholder='Enter your name'
                                  value={name}
                                  onChange={(e) => setName(e.target.value)}
                                />
                              </Form.Group>
                            </>
                          )}

                          {/* COMMUN FIELDS */}
                          <Form onSubmit={handleSubmit}>
                            <Form.Group className='mb-3 mt-3'>
                              <Form.Label>Email</Form.Label>
                              <Form.Control
                                type='text'
                                placeholder='Enter your email'
                                value={email}
                                onChange={(e) => setemail(e.target.value)}
                              />
                            </Form.Group>

                            <Form.Group className='mb-3'>
                              <Form.Label>Password</Form.Label>
                              <Form.Control
                                type='password'
                                placeholder='Enter your password'
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                              />
                            </Form.Group>

                            {/* ERROR DISPLAY */}
                            {authError && (
                              <Alert variant='danger'>{authError}</Alert>
                            )}

                            {/* SUBMIT FORM BUTTON */}
                            <Button
                              type='submit'
                              disabled={isSubmitting}
                              className='w-100 mt-3 button'
                            >
                              {isSubmitting ? (
                                <Spinner
                                  as='span'
                                  animation='border'
                                  size='sm'
                                  role='status'
                                  aria-hidden='true'
                                />
                              ) : activeTab === "login" ? (
                                "Login"
                              ) : (
                                "Sign Up"
                              )}
                            </Button>
                            <Button className='w-100 mt-3 button' href='/'>
                              Back to Home
                            </Button>
                          </Form>
                        </Col>
                      </Row>
                    </Container>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>
    </>
  );
}
