/**
 * Copyright 2018, Radiant Solutions, Inc.
 * 
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 * 
 *   http://www.apache.org/licenses/LICENSE-2.0
 * 
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 **/
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
	
	@Test
	public void testRuntimeExceptionWrappedUserException() {
		UserException ue = new UserException("test message", "test details", HttpStatus.I_AM_A_TEAPOT);
		RuntimeException re = new RuntimeException(ue);
		
		ResponseEntity<String> response = this.userExceptionHandler.handleRuntimeException(re);
		
		assertEquals(response.getBody(), "test message");
		assertEquals(response.getStatusCodeValue(), HttpStatus.I_AM_A_TEAPOT.value());
		assertEquals(response.getHeaders().get("Content-Type").get(0), "text/plain");
	}
	
	@Test
	public void testRuntimeExceptionNoCause() {
		RuntimeException re = new RuntimeException("test message");
		
		ResponseEntity<String> response = this.userExceptionHandler.handleRuntimeException(re);
		
		assertEquals(response.getBody(), "test message");
		assertEquals(response.getStatusCodeValue(), HttpStatus.INTERNAL_SERVER_ERROR.value());
		assertEquals(response.getHeaders().get("Content-Type").get(0), "text/plain");
	}
	
}
