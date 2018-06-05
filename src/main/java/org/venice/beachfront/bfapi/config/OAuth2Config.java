package org.venice.beachfront.bfapi.config;

import java.io.IOException;
import java.net.URL;
import java.util.Arrays;
import java.util.Map;
import java.util.UUID;

import javax.servlet.http.Cookie;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

import org.apache.commons.codec.binary.Base64;
import org.joda.time.DateTime;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.HttpStatus;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.oauth2.client.OAuth2ClientContext;
import org.springframework.security.oauth2.client.OAuth2RestTemplate;
import org.springframework.security.oauth2.client.resource.OAuth2ProtectedResourceDetails;
import org.springframework.security.oauth2.client.token.AccessTokenProvider;
import org.springframework.security.oauth2.client.token.AccessTokenProviderChain;
import org.springframework.security.oauth2.client.token.grant.client.ClientCredentialsAccessTokenProvider;
import org.springframework.security.oauth2.client.token.grant.code.AuthorizationCodeAccessTokenProvider;
import org.springframework.security.oauth2.client.token.grant.implicit.ImplicitAccessTokenProvider;
import org.springframework.security.oauth2.client.token.grant.password.ResourceOwnerPasswordAccessTokenProvider;
import org.springframework.security.oauth2.common.OAuth2AccessToken;
import org.springframework.security.oauth2.config.annotation.web.configuration.EnableOAuth2Client;
import org.springframework.security.web.authentication.logout.SecurityContextLogoutHandler;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestMethod;
import org.springframework.web.util.UriComponentsBuilder;
import org.venice.beachfront.bfapi.auth.OpenIDTokenProvider;
import org.venice.beachfront.bfapi.model.UserProfile;
import org.venice.beachfront.bfapi.model.exception.UserException;
import org.venice.beachfront.bfapi.services.UserProfileService;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;

@Configuration
@Controller
@EnableOAuth2Client
public class OAuth2Config {

    // property set by spring-cloud-sso-connector
    @Value("${ssoServiceUrl:placeholder}")
	private String ssoServiceUrl;

	@Value("${security.oauth2.client.clientId:placeholder}")
	private String clientId;

	@Value("${DOMAIN}")
	private String domain;

	@Value("${cookie.expiry.seconds}")
	private int cookieExpirySeconds;

	@Value("${cookie.name}")
	private String cookieName;

	@Autowired
	private ObjectMapper objectMapper;

	@Autowired
	private OAuth2ClientContext oAuth2ClientContext;

	@Autowired
	private OAuth2ProtectedResourceDetails resourceDetails;

	@Autowired
	private UserProfileService userProfileService;

    @Bean
    public OAuth2RestTemplate oauth2RestTemplate() {
    	final OAuth2RestTemplate oauth2RestTemplate = new OAuth2RestTemplate(resourceDetails, oAuth2ClientContext);
        oauth2RestTemplate.setAccessTokenProvider(accessTokenProviderChain());

        return oauth2RestTemplate;
    }

    @Bean
    public AccessTokenProvider accessTokenProviderChain() {
        return new AccessTokenProviderChain(Arrays.<AccessTokenProvider> asList(
            new OpenIDTokenProvider(),
            new AuthorizationCodeAccessTokenProvider(),
            new ImplicitAccessTokenProvider(),
            new ResourceOwnerPasswordAccessTokenProvider(),
            new ClientCredentialsAccessTokenProvider()));
    }

    @RequestMapping("/oauth/start")
    public String startOAuth(final Model model, final HttpServletRequest request, final HttpServletResponse response) throws Exception {

    	if (ssoServiceUrl.equals("placeholder")) {
            model.addAttribute("header", "Warning: You need to bind to the SSO service.");
            model.addAttribute("warning", "Please bind your app to restore regular functionality");
            return "configure_warning";
        }

        // Get information for the User from the /userinfo endpoint available on the SSO Tile
        final Map<?,?> userInfoResponse = oauth2RestTemplate().getForObject("{ssoServiceUrl}/userinfo", Map.class, ssoServiceUrl);
        model.addAttribute("ssoServiceUrl",ssoServiceUrl);
        model.addAttribute("response", toPrettyJsonString(userInfoResponse));

        // Get Access Token
        final OAuth2AccessToken accessToken = oauth2RestTemplate().getOAuth2ClientContext().getAccessToken();
        if (accessToken != null) {
            model.addAttribute("access_token", toPrettyJsonString(parseToken(accessToken.getValue())));
            model.addAttribute("id_token", toPrettyJsonString(parseToken((String) accessToken.getAdditionalInformation().get("id_token"))));
        }

        // Confirm User Profile exists; if not, create
        final String userId = (String) userInfoResponse.get("user_id");
        final String userName = (String) userInfoResponse.get("user_name");
        final UserProfile userProfile = getOrCreateUser(userId, userName);

        // Build Response
        final String uiRedirectUri = UriComponentsBuilder.newInstance().scheme("https").host("beachfront." + this.domain).queryParam("logged_in", "true").build().toUri().toString();
        final Cookie cookie = createCookie(userProfile.getApiKey(), cookieExpirySeconds);

        response.addCookie(cookie);
        response.setStatus(HttpStatus.FOUND.value());
        response.setHeader("Location", uiRedirectUri);

        return "authorization_code";
    }

    @RequestMapping(value="/logout", method = RequestMethod.GET)
    public String logout(final HttpServletRequest request, final HttpServletResponse response, final Authentication authentication) throws IOException, UserException {

    	final Authentication auth = SecurityContextHolder.getContext().getAuthentication();
        if (auth != null){
            new SecurityContextLogoutHandler().logout(request, response, auth);
        }
		final URL url = new URL(request.getRequestURL().toString());
		final String urlStr = url.getProtocol() + "://" + url.getAuthority();

		// Server-side invalidation of API Key
		final UserProfile userProfile = userProfileService.getProfileFromAuthentication(authentication);
		userProfileService.invalidateKey(userProfile);

		// Clear the session cookie
		response.addCookie(createCookie(null, 0));
		response.setStatus(HttpStatus.OK.value());

        return "redirect:" + ssoServiceUrl + "/logout.do?redirect=" + urlStr + "&clientId=" + clientId;
    }

    private Map<String, ?> parseToken(final String base64Token) throws IOException {
        final String token = base64Token.split("\\.")[1];
        return objectMapper.readValue(Base64.decodeBase64(token), new TypeReference<Map<String, ?>>() { });
    }

	private String toPrettyJsonString(final Object object) throws Exception {
	    return objectMapper.writerWithDefaultPrettyPrinter().writeValueAsString(object);
	}

	private UserProfile getOrCreateUser(final String userId, final String userName) {

		UserProfile user = userProfileService.getUserProfileById(userId);

		if (user != null) {

			// Check if the user has a current API Key
			if (user.getApiKey() == null) {

				// Generate a new API Key if the user exists, but has no existing key
				user.setApiKey(generateApiKey());
				userProfileService.updateLastAccessed(user);
			}
		}
		else {
			final String apiKey = generateApiKey();
			user = new UserProfile(userId, userName, apiKey, DateTime.now());
			userProfileService.saveUserProfile(user);
		}

		return user;
	}

	private String generateApiKey() {
		return UUID.randomUUID().toString();
	}

	private Cookie createCookie(final String apiKey, final int expiry) {
		final Cookie cookie = new Cookie(cookieName, apiKey);
		cookie.setDomain(domain);
		cookie.setSecure(true);
		cookie.setPath("/");
		cookie.setMaxAge(expiry);
		return cookie;
	}
}
