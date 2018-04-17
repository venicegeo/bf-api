package org.venice.beachfront.bfapi.model.oauth;

import java.io.File;
import java.io.IOException;

import org.apache.commons.io.IOUtils;
import org.junit.Assert;
import org.junit.Before;
import org.junit.Test;

import com.fasterxml.jackson.databind.ObjectMapper;

public class ProfileResponseBodyTests {
	private ObjectMapper objectMapper;
	
	@Before
	public void setup() {
		this.objectMapper= new ObjectMapper();
	}
	
	@Test
	public void testParseSingleCNGeoAxisBody() throws IOException {
		// Mock
		String responseJson = IOUtils.toString(
				this.getClass().getClassLoader().getResourceAsStream(String.format("%s%s%s", "model", File.separator, "geoaxis-single-cn.json")),
				"UTF-8");
		
		// Test
		ProfileResponseBody body = this.objectMapper.readerFor(ProfileResponseBody.class).readValue(responseJson);
		
		// Asserts
		Assert.assertEquals("distinguished-name.test.localdomain", body.getDn());
		Assert.assertEquals("testuser.localdomain", body.getCommonName());
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
		ProfileResponseBody body = this.objectMapper.readerFor(ProfileResponseBody.class).readValue(responseJson);
		
		// Asserts
		Assert.assertEquals("distinguished-name.test.localdomain", body.getDn());
		Assert.assertEquals("testuser.localdomain", body.getCommonName());
		Assert.assertEquals("testorg.localdomain", body.getMemberOf());
		Assert.assertEquals("FirstName", body.getFirstname());
		Assert.assertEquals("LastName", body.getLastname());
		Assert.assertEquals("test-id-123", body.getId());
	}
}
