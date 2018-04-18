package org.venice.beachfront.bfapi.model.oauth;

import java.io.IOException;
import java.util.Collections;
import java.util.LinkedList;
import java.util.List;

import com.fasterxml.jackson.core.JsonParseException;
import com.fasterxml.jackson.core.JsonParser;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.core.TreeNode;
import com.fasterxml.jackson.databind.DeserializationContext;
import com.fasterxml.jackson.databind.JsonDeserializer;
import com.fasterxml.jackson.databind.JsonNode;

public interface AbstractCommonName {
	public String toString();
	
	public static class Deserializer extends JsonDeserializer<AbstractCommonName> {
		@Override
		public AbstractCommonName deserialize(JsonParser p, DeserializationContext ctxt) throws IOException, JsonProcessingException {
			TreeNode node = p.getCodec().readTree(p);
			if (node.isValueNode() && ((JsonNode)node).isTextual()) {
				return new SingleString(((JsonNode)node).asText());
			}
			if (node.isArray()) {
				LinkedList<String> cns = new LinkedList<>();
				for (int i=0; i < node.size(); i++) {
					if (!node.get(i).isValueNode()) {
						throw new JsonParseException(p, "Non-string element found in commonname array: " + node.toString());						
					}
					cns.add(((JsonNode)node.get(i)).asText());
				}
				if (cns.size() < 1) {
					throw new JsonParseException(p, "Empty commonname array");
				}
				return new StringList(cns);
			}
			throw new JsonParseException(p, "Could not parse commonname");						
		}
	}
	
	public static class SingleString implements AbstractCommonName {
		private String commonName;
		public SingleString(String commonName) {
			this.commonName = commonName;
		}
		
		@Override
		public String toString() {
			return this.commonName;
		}
	}
	
	public static class StringList implements AbstractCommonName {
		private List<String> commonName;
		public StringList(List<String> commonName) {
			this.commonName = Collections.unmodifiableList(commonName);
		}

		@Override
		public String toString() {
			// Only return the first common name in the list
			return this.commonName.get(0);
		}
	}
}