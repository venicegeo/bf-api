package org.venice.beachfront.bfapi.auth.jwt;

import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;

public class JWTToken extends UsernamePasswordAuthenticationToken {

	public JWTToken(Object principal, Object credentials) {
		super(principal, credentials);
		// TODO Auto-generated constructor stub
	}

}
