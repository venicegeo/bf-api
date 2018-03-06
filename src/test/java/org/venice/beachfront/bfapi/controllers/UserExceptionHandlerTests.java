package org.venice.beachfront.bfapi.controllers;

import static org.junit.Assert.assertEquals;

import org.junit.Before;
import org.junit.Test;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.MockitoAnnotations;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.venice.beachfront.bfapi.model.exception.UserException;

import util.PiazzaLogger;

public class UserExceptionHandlerTests {
	@Mock
	private PiazzaLogger piazzaLogger;

	@InjectMocks
	private UserExceptionHandler userExceptionHandler;

	@Before
	public void setup() throws UserException {
		MockitoAnnotations.initMocks(this);
	}
	
	@Test
	public void testPlainTextExceptionOutput() {
		UserException ue = new UserException("test message", "test details", HttpStatus.I_AM_A_TEAPOT);
		
		ResponseEntity<String> response = this.userExceptionHandler.handleUserException(ue);
		
		assertEquals(response.getBody(), "test message");
		assertEquals(response.getStatusCodeValue(), HttpStatus.I_AM_A_TEAPOT.value());
		assertEquals(response.getHeaders().get("Content-Type").get(0), "text/plain");
	}
}
