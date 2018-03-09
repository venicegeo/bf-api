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

import java.io.BufferedWriter;
import java.io.PrintWriter;
import java.io.StringWriter;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
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
		this.logger.log(logMessage, Severity.ERROR);
		return ResponseEntity.status(ex.getRecommendedStatusCode())
				.contentType(MediaType.TEXT_PLAIN)
				.body(ex.getMessage());
	}
	
	@ExceptionHandler(RuntimeException.class)
	public ResponseEntity<String> handleRuntimeException(RuntimeException ex) {
		if (ex.getCause() != null && ex.getCause().getClass() == UserException.class) {
			return this.handleUserException((UserException)ex.getCause());
		}
		String logMessage = String.format("[500] Unknown runtime error -- %s", ex.getMessage());
		this.logger.log(logMessage, Severity.ERROR);
		
		StringWriter sw = new StringWriter();
		ex.printStackTrace(new PrintWriter(sw));
		this.logger.log(sw.toString(), Severity.ERROR);
		
		return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
			.contentType(MediaType.TEXT_PLAIN)
			.body(ex.getMessage());
	}
}
