package org.venice.beachfront.bfapi.controllers;

import java.net.URI;
import java.net.URISyntaxException;
import java.util.concurrent.CompletableFuture;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestMethod;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.ResponseBody;
import org.venice.beachfront.bfapi.model.Scene;
import org.venice.beachfront.bfapi.services.IABrokerService;

/**
 * Main controller class for managing and downloading scenes.
 * 
 * @version 1.0
 */
@Controller
public class SceneController {
	private IABrokerService iaBrokerService;
	
	@Autowired
	public SceneController(IABrokerService iaBrokerService) {
		this.iaBrokerService = iaBrokerService;
	}
	
	@RequestMapping(
			path="/scene/{id}/download",
			method=RequestMethod.GET,
			params={"planet_api_key"})
	@ResponseBody
	public CompletableFuture<ResponseEntity<?>> downloadScene(
			@PathVariable(value="id") String sceneId,
			@RequestParam(value="planet_api_key", required=true) String planetApiKey
			) {
		Scene scene = this.iaBrokerService.getScene(sceneId, planetApiKey, true);
	
		return this.iaBrokerService.asyncActivateScene(scene, planetApiKey)
				.thenApply((String resourceUrl) -> {
					HttpHeaders headers = new HttpHeaders();
					try {
						headers.setLocation(new URI(resourceUrl));
					} catch (URISyntaxException e) {
						throw new RuntimeException(e);
					}
					return ResponseEntity.status(HttpStatus.FOUND).headers(headers).build();
				});
	}
}
