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
package org.venice.beachfront.bfapi.model.converter;

import javax.persistence.AttributeConverter;
import javax.persistence.Converter;

import org.springframework.beans.factory.annotation.Autowired;
import org.venice.beachfront.bfapi.database.dao.UserProfileDao;
import org.venice.beachfront.bfapi.model.UserProfile;

@Converter(autoApply = true)
public class UserConverter implements AttributeConverter<UserProfile, String>, org.springframework.core.convert.converter.Converter<String, UserProfile> {
    @Autowired
    UserProfileDao userProfileDao;

    @Override
    public String convertToDatabaseColumn(UserProfile user) {
         if (user == null) {
            return null;
         }
         return user.getUserId();
    }

    @Override
    public UserProfile convertToEntityAttribute(String userId) {
         if (userId == null) {
            return null;
         }
         return userProfileDao.findByUserId(userId);
    }

    @Override
    public UserProfile convert(String userId) {
        return convertToEntityAttribute(userId);
    }
}
