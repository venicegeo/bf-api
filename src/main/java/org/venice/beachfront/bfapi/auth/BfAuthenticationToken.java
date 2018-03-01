package org.venice.beachfront.bfapi.auth;

import java.util.Collections;

import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;

public class BfAuthenticationToken extends UsernamePasswordAuthenticationToken {
	private static final long serialVersionUID = 1L;

	public BfAuthenticationToken(Object principal, Object credentials) {
		super(principal, credentials, Collections.emptyList());
	}

}
