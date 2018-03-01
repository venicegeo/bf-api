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
