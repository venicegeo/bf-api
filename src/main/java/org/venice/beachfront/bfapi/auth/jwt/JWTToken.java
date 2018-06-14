package org.venice.beachfront.bfapi.auth.jwt;

import org.springframework.security.authentication.AbstractAuthenticationToken;
import org.springframework.security.core.authority.AuthorityUtils;

public class JWTToken extends AbstractAuthenticationToken {

	public JWTToken(Object c, Object p) {
		super(AuthorityUtils.NO_AUTHORITIES);
	}
	
	@Override
	public Object getCredentials() {
		// TODO Auto-generated method stub
		return null;
	}

	@Override
	public Object getPrincipal() {
		// TODO Auto-generated method stub
		return null;
	}



}
