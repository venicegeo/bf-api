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

import java.io.PrintWriter;
import java.io.StringWriter;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.http.converter.HttpMessageNotReadableException;
import org.springframework.web.bind.annotation.ControllerAdvice;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.venice.beachfront.bfapi.model.exception.UserException;

import model.logger.Severity;
import util.PiazzaLogger;

@ControllerAdvice
public class UserExceptionHandler {
	@Autowired
	private PiazzaLogger logger;

	@ExceptionHandler(UserException.class)
	public ResponseEntity<String> handleUserException(UserException ex) {
		String logMessage = String.format("[%d] %s -- %s", ex.getRecommendedStatusCode().value(), ex.getMessage(), ex.getDetails());
		logger.log(logMessage, Severity.ERROR);
		return ResponseEntity.status(ex.getRecommendedStatusCode()).contentType(MediaType.TEXT_PLAIN).body(ex.getMessage());
	}

	@ExceptionHandler(RuntimeException.class)
	public ResponseEntity<String> handleRuntimeException(RuntimeException ex) {
		HttpStatus status = HttpStatus.INTERNAL_SERVER_ERROR;
		if (ex.getCause() != null && ex.getCause().getClass() == UserException.class) {
			// Handle User Exceptions separately
			return this.handleUserException((UserException) ex.getCause());
		} else if (ex.getCause() != null && ex.getCause().getClass() == HttpMessageNotReadableException.class) {
			// Message parse errors return 400
			status = HttpStatus.BAD_REQUEST;
		}
		String logMessage = String.format("[%d] Unknown runtime error -- %s", status.value(), ex.getMessage());
		logger.log(logMessage, Severity.ERROR);

		StringWriter sw = new StringWriter();
		ex.printStackTrace(new PrintWriter(sw));
		logger.log(sw.toString(), Severity.ERROR);

		return ResponseEntity.status(status).contentType(MediaType.TEXT_PLAIN).body(ex.getMessage());
	}
}
