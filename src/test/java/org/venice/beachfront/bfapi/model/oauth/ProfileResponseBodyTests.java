package org.venice.beachfront.bfapi.model.oauth;

import java.io.File;
import java.io.IOException;
import java.util.Arrays;
import org.apache.commons.io.IOUtils;
import org.junit.Assert;
import org.junit.Before;
import org.junit.Test;
import org.mockito.MockitoAnnotations;
import org.mockito.Spy;
import org.springframework.http.HttpStatus;
import org.venice.beachfront.bfapi.model.exception.UserException;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.module.SimpleModule;

public class ProfileResponseBodyTests {
	@Spy
	private ObjectMapper objectMapper;
	
	@Before
	public void setup() {
		MockitoAnnotations.initMocks(this);

		SimpleModule module = new SimpleModule();
		module.addDeserializer(GeoAxisCommonName.class, new GeoAxisCommonName.Deserializer());
		this.objectMapper.registerModule(module);
	}
	
	
	@Test
	public void testParseSingleCNGeoAxisBody() throws IOException {
		// Mock
		String responseJson = IOUtils.toString(
				this.getClass().getClassLoader().getResourceAsStream(String.format("%s%s%s", "model", File.separator, "geoaxis-single-cn.json")),
				"UTF-8");
		
		// Test
		ProfileResponseBody body = objectMapper.readValue(responseJson, ProfileResponseBody.class);
		
		// Asserts
		Assert.assertEquals("distinguished-name.test.localdomain", body.getDn());
		Assert.assertEquals("testuser.localdomain", body.getCommonName().toString());
		Assert.assertEquals("testorg.localdomain", body.getMemberOf());
		Assert.assertEquals("FirstName", body.getFirstname());
		Assert.assertEquals("LastName", body.getLastname());
		Assert.assertEquals("test-id-123", body.getId());
	}

	@Test
	public void testParseMultiCNGeoAxisBody() throws IOException {
		// Mock
		String responseJson = IOUtils.toString(
				this.getClass().getClassLoader().getResourceAsStream(String.format("%s%s%s", "model", File.separator, "geoaxis-multi-cn.json")),
				"UTF-8");
		
		// Test
		ProfileResponseBody body = objectMapper.readValue(responseJson, ProfileResponseBody.class);
		
		// Asserts
		Assert.assertEquals("distinguished-name.test.localdomain", body.getDn());
		Assert.assertEquals("testuser1.localdomain", body.getCommonName().toString());
		Assert.assertEquals("testorg.localdomain", body.getMemberOf());
		Assert.assertEquals("FirstName", body.getFirstname());
		Assert.assertEquals("LastName", body.getLastname());
		Assert.assertEquals("test-id-123", body.getId());
	}
	
	@Test
	public void testComputedUserIdPriorities() throws UserException {
		// Mock
		ProfileResponseBody fullBody = new ProfileResponseBody("distinguished-name", new GeoAxisCommonName.SingleString("common-name"), "member-of", "first-name", "last-name", "id");
		ProfileResponseBody dnBody = new ProfileResponseBody("distinguished-name", new GeoAxisCommonName.SingleString("common-name"), "member-of", null, null, null);
		ProfileResponseBody singleCNBody = new ProfileResponseBody(null, new GeoAxisCommonName.SingleString("common-name"), "member-of", null, null, null);
		ProfileResponseBody multiCNBody = new ProfileResponseBody(null, new GeoAxisCommonName.StringList(Arrays.asList("common-name-1", "common-name-2")) , "member-of", null, null, null);
		ProfileResponseBody nameIdBody = new ProfileResponseBody(null, null, null, "firstname", "lastname", "id");
		ProfileResponseBody invalidBody = new ProfileResponseBody(null, null, null, null, null, null);

		// Asserts
		Assert.assertEquals("distinguished-name", fullBody.getComputedUserId());
		Assert.assertEquals("distinguished-name", dnBody.getComputedUserId());
		Assert.assertEquals("common-name@member-of", singleCNBody.getComputedUserId());
		Assert.assertEquals("common-name-1@member-of", multiCNBody.getComputedUserId());
		Assert.assertEquals("id@lastname-firstname", nameIdBody.getComputedUserId());
		try {
			String id = invalidBody.getComputedUserId();
			Assert.fail("expected exception getting invalid user id, instead got: " + id);
		} catch (UserException e) {
			Assert.assertTrue(e.getMessage().contains("Could not obtain a user ID from OAuth profile response"));
			Assert.assertEquals(HttpStatus.INTERNAL_SERVER_ERROR, e.getRecommendedStatusCode());
		}
	}
	
	@Test
	public void testComputedUserNamePriorities() throws UserException {
		// Mock
		ProfileResponseBody fullBody = new ProfileResponseBody("distinguished-name", new GeoAxisCommonName.SingleString("common-name"), "member-of", "first-name", "last-name", "id");
		ProfileResponseBody dnBody = new ProfileResponseBody("distinguished-name", new GeoAxisCommonName.SingleString("common-name"), "member-of", null, null, null);
		ProfileResponseBody singleCNBody = new ProfileResponseBody(null, new GeoAxisCommonName.SingleString("common-name"), "member-of", null, null, null);
		ProfileResponseBody multiCNBody = new ProfileResponseBody(null, new GeoAxisCommonName.StringList(Arrays.asList("common-name-1", "common-name-2")) , "member-of", null, null, null);
		ProfileResponseBody nameIdBody = new ProfileResponseBody(null, null, null, "firstname", "lastname", "id");
		ProfileResponseBody invalidBody = new ProfileResponseBody(null, null, null, null, null, null);

		// Asserts
		Assert.assertEquals("common-name", fullBody.getComputedUserName());
		Assert.assertEquals("common-name", dnBody.getComputedUserName());
		Assert.assertEquals("common-name", singleCNBody.getComputedUserName());
		Assert.assertEquals("common-name-1", multiCNBody.getComputedUserName());
		Assert.assertEquals("id", nameIdBody.getComputedUserName());
		try {
			String username = invalidBody.getComputedUserName();
			Assert.fail("expected exception getting invalid user name, instead got: " + username);
		} catch (UserException e) {
			Assert.assertTrue(e.getMessage().contains("Could not obtain a user name from OAuth profile response"));
			Assert.assertEquals(HttpStatus.INTERNAL_SERVER_ERROR, e.getRecommendedStatusCode());
		}
	}
}
