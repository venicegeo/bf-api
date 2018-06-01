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
import com.fasterxml.jackson.databind.annotation.JsonDeserialize;

/**
 * AbstractCommonName is a polymorphic interface intended to enable parsing
 * of OAuth profile responses that can have their CN listed either as a
 * single string or a list of strings. For supporting this use case, Jackson
 * requires a custom deserializer, which is implemented here, along with 
 * some container classes for the different forms of CN data.
 */
@JsonDeserialize(using = AbstractStringList.Deserializer.class)
public interface AbstractStringList {
	public String toString();
	
	public static class Deserializer extends JsonDeserializer<AbstractStringList> {
		@Override
		public AbstractStringList deserialize(JsonParser p, DeserializationContext ctxt) throws IOException, JsonProcessingException {
			TreeNode node = p.getCodec().readTree(p);
			if (node.isValueNode() && ((JsonNode)node).isTextual()) {
				return new SingleString(((JsonNode)node).asText());
			}
			if (node.isArray()) {
				LinkedList<String> cns = new LinkedList<>();
				for (int i=0; i < node.size(); i++) {
					if (!node.get(i).isValueNode()) {
						throw new JsonParseException(p, "Non-string element found in string array: " + node.toString());
					}
					cns.add(((JsonNode)node.get(i)).asText());
				}
				if (cns.size() < 1) {
					throw new JsonParseException(p, "Empty string array");
				}
				return new StringList(cns);
			}
			throw new JsonParseException(p, "Could not parse string");
		}
	}
	
	public static class SingleString implements AbstractStringList {
		private String singleString;
		public SingleString(String singleString) {
			this.singleString = singleString;
		}
		
		@Override
		public String toString() {
			return this.singleString;
		}
	}
	
	public static class StringList implements AbstractStringList {
		private List<String> stringList;
		public StringList(List<String> stringList) {
			this.stringList = Collections.unmodifiableList(stringList);
		}

		@Override
		public String toString() {
			// Only return the first common name in the list
			return this.stringList.get(0);
		}
	}
}