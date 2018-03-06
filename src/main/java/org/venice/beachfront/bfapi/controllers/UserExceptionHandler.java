package org.venice.beachfront.bfapi.controllers;

import org.springframework.beans.factory.annotation.Autowired;
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
}
