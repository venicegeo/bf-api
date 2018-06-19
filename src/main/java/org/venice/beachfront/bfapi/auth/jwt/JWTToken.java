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
package org.venice.beachfront.bfapi.auth.jwt;

import org.springframework.security.authentication.AbstractAuthenticationToken;
import org.springframework.security.core.authority.AuthorityUtils;

/**
 * Simple wrapper class for a JWT Authentication Token. This will pass the cmoplete, encoded JWT as the Principal.
 * 
 * @author Patrick.Doody
 *
 */
public class JWTToken extends AbstractAuthenticationToken {
	private String tokenPrincipal;

	public JWTToken(String tokenPrincipal) {
		super(AuthorityUtils.NO_AUTHORITIES);
		this.tokenPrincipal = tokenPrincipal;
	}

	@Override
	public Object getPrincipal() {
		return tokenPrincipal;
	}

	@Override
	public Object getCredentials() {
		return null;
	}
}
